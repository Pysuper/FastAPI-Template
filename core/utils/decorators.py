import asyncio
import functools
import time
from typing import Any, Callable, TypeVar, cast

from fastapi import Request
from pydantic import BaseModel

from core.core.logic import UnifiedLogger
from core.utils.helpers import format_exception

T = TypeVar("T")
logger = UnifiedLogger("decorators")


class CacheConfig(BaseModel):
    """缓存配置"""

    key_prefix: str = ""
    ttl: int = 3600  # 默认1小时

    class Config:
        extra = "allow"


def get_cache():
    pass


def cache(key_prefix: str, ttl: int = 3600, cache_null: bool = False) -> Callable:
    """缓存装饰器"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:

            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            cache_client = get_cache()

            # 尝试从缓存获取
            cached_value = await cache_client.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 如果结果为None且不缓存None，直接返回
            if result is None and not cache_null:
                return None

            # 缓存结果
            await cache_client.set(cache_key, result, expire=ttl)
            return result

        return cast(Callable[..., T], wrapper)

    return decorator


def retry(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)) -> Callable:
    """重试装饰器"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_retries} failed",
                            extra={"function": func.__name__, "error": format_exception(e), "attempt": attempt + 1},
                        )
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception

        return cast(Callable[..., T], wrapper)

    return decorator


def validate_request(model: type[BaseModel]) -> Callable:
    """请求验证装饰器"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            # 验证请求数据
            try:
                body = await request.json()
                validated_data = model(**body)
                kwargs["validated_data"] = validated_data
                return await func(request, *args, **kwargs)
            except Exception as e:
                logger.error(
                    "Request validation failed", extra={"error": format_exception(e), "body": await request.body()}
                )
                raise

        return cast(Callable[..., T], wrapper)

    return decorator


def rate_limit(key: str, limit: int, period: int = 60, by_ip: bool = True) -> Callable:
    """限流装饰器"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:

            # 生成限流键
            client_ip = request.client.host if by_ip else ""
            rate_key = f"rate_limit:{key}:{client_ip}:{int(time.time() / period)}"

            # 检查限流
            cache_client = get_cache()
            current = await cache_client.incr(rate_key)
            if current == 1:
                await cache_client.expire(rate_key, period)

            if current > limit:
                from ..exceptions.base import RateLimitExceeded

                raise RateLimitExceeded()

            return await func(request, *args, **kwargs)

        return cast(Callable[..., T], wrapper)

    return decorator


def log_request(func: Callable[..., T]) -> Callable[..., T]:
    """请求日志装饰器"""

    @functools.wraps(func)
    async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        response = None

        try:
            # 记录请求开始
            logger.info(
                "Request started",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                },
            )

            # 执行请求
            response = await func(request, *args, **kwargs)
            return response

        except Exception as e:
            # 记录异常
            logger.error(
                "Request failed",
                extra={"error": format_exception(e), "method": request.method, "path": request.url.path},
            )
            raise

        finally:
            # 记录请求完成
            process_time = time.time() - start_time
            status_code = getattr(response, "status_code", 500)

            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "process_time": process_time,
                },
            )

    return cast(Callable[..., T], wrapper)
