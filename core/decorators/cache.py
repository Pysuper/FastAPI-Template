import json
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional, Union
from typing import TypeVar

from cache.config.config import CacheConfig
from core.cache.base.enums import CacheStrategy, CacheLevel, SerializationFormat
from core.cache.manager import cache_manager
from utils.redis_cli import redis_client

T = TypeVar("T")


def cache_result(
    key_pattern: str,
    *,
    ttl: Optional[int] = None,
    strategy: CacheStrategy = CacheStrategy.REDIS,
    level: CacheLevel = CacheLevel.PRIVATE,
    serialization: SerializationFormat = SerializationFormat.JSON,
    prefix: str = "",
    version: str = "v1",
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    缓存函数结果
    :param key_pattern: 缓存键模式
    :param ttl: 过期时间（秒）
    :param strategy: 缓存策略
    :param level: 缓存级别
    :param serialization: 序列化格式
    :param prefix: 键前缀
    :param version: 缓存版本
    :param key_builder: 自定义键构建函数
    """
    return cache_manager.cache(
        key_pattern,
        ttl=ttl,
        strategy=strategy,
        level=level,
        serialization=serialization,
        prefix=prefix,
        version=version,
    )


def cache_invalidate(
    key_pattern: str,
    *,
    prefix: str = "",
    version: str = "v1",
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    使缓存失效
    :param key_pattern: 缓存键模式
    :param prefix: 键前缀
    :param version: 缓存版本
    :param key_builder: 自定义键构建函数
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_values = {
                    **kwargs,
                    **{f"arg{i}": arg for i, arg in enumerate(args) if isinstance(arg, (str, int, float, bool))},
                }
                cache_key = key_pattern.format(**key_values)

            # 执行原函数
            result = await func(*args, **kwargs)

            # 删除缓存
            config = CacheConfig(strategy=CacheStrategy.BOTH, prefix=prefix, version=version)
            await cache_manager.delete(cache_key, config=config)

            return result

        return wrapper

    return decorator


def http_cache(
    *,
    ttl: Optional[int] = None,
    level: CacheLevel = CacheLevel.PRIVATE,
    vary_by_headers: Optional[list[str]] = None,
):
    """
    HTTP响应缓存
    :param ttl: 过期时间（秒）
    :param level: 缓存级别
    :param vary_by_headers: 变化的请求头
    """
    return cache_manager.http_cache(
        ttl=ttl,
        level=level,
        vary_by_headers=vary_by_headers,
    )


def bulk_cache_invalidate(patterns: list[str], *, prefix: str = "", version: str = "v1"):
    """
    批量使缓存失效
    :param patterns: 缓存键模式列表
    :param prefix: 键前缀
    :param version: 缓存版本
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 执行原函数
            result = await func(*args, **kwargs)

            # 删除所有匹配的缓存
            config = CacheConfig(strategy=CacheStrategy.BOTH, prefix=prefix, version=version)
            for pattern in patterns:
                key_values = {
                    **kwargs,
                    **{f"arg{i}": arg for i, arg in enumerate(args) if isinstance(arg, (str, int, float, bool))},
                }
                cache_key = pattern.format(**key_values)
                await cache_manager.delete(cache_key, config=config)

            return result

        return wrapper

    return decorator


def cache_method(
    key_pattern: str,
    *,
    ttl: Optional[int] = None,
    strategy: CacheStrategy = CacheStrategy.REDIS,
    level: CacheLevel = CacheLevel.PRIVATE,
    serialization: SerializationFormat = SerializationFormat.JSON,
    prefix: str = "",
    version: str = "v1",
):
    """
    缓存类方法结果
    :param key_pattern: 缓存键模式
    :param ttl: 过期时间（秒）
    :param strategy: 缓存策略
    :param level: 缓存级别
    :param serialization: 序列化格式
    :param prefix: 键前缀
    :param version: 缓存版本
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 构建缓存键
            key_values = {
                **kwargs,
                **{f"arg{i}": arg for i, arg in enumerate(args) if isinstance(arg, (str, int, float, bool))},
                "self": getattr(self, "id", str(self)),
            }
            cache_key = key_pattern.format(**key_values)

            config = CacheConfig(
                strategy=strategy,
                ttl=ttl,
                level=level,
                serialization=serialization,
                prefix=prefix,
                version=version,
            )

            # 尝试从缓存获取
            cached_value = await cache_manager.get(cache_key, config=config)
            if cached_value is not None:
                return cached_value

            # 执行原函数
            result = await func(self, *args, **kwargs)

            # 存入缓存
            await cache_manager.set(cache_key, result, config=config)

            return result

        return wrapper

    return decorator


def cache(prefix: str, ttl: Optional[Union[int, timedelta]] = None, key_builder: Callable[..., str] = None):
    """
    缓存装饰器
    用法:
    @cache("user", ttl=300)
    async def get_user(user_id: int) -> dict:
        ...

    @cache("user", key_builder=lambda user_id, **kwargs: f"custom:{user_id}")
    async def get_user(user_id: int) -> dict:
        ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 构建缓存键
            if key_builder:
                cache_key = f"{prefix}:{key_builder(*args, **kwargs)}"
            else:
                # 默认使用参数值构建键
                key_parts = [str(arg) for arg in args]
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{prefix}:{':'.join(key_parts)}"

            # 确保 Redis 客户端已初始化
            if not redis_client.client:
                await redis_client.init()

            # 尝试从缓存获取
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 执行原函数
            result = await func(*args, **kwargs)

            # 存入缓存
            await redis_client.set(cache_key, json.dumps(result), expire=ttl)

            return result

        return wrapper

    return decorator


def cache_invalidate(prefix: str, key_pattern: str = None):
    """
    缓存失效装饰器
    用法:
    @cache_invalidate("user", "user:{user_id}")
    async def update_user(user_id: int, **data) -> dict:
        ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 执行原函数
            result = await func(*args, **kwargs)

            # 构建缓存键模式
            if key_pattern:
                pattern = f"{prefix}:{key_pattern.format(**kwargs)}"
            else:
                pattern = f"{prefix}:*"

            # 删除匹配的缓存
            async for key in redis_client.client.scan_iter(match=pattern):
                await redis_client.delete(key)

            return result

        return wrapper

    return decorator


def rate_limit(key: str, limit: int, period: Union[int, timedelta], scope: str = "default"):
    """
    速率限制装饰器
    用法:
    @rate_limit("login", limit=5, period=300)  # 5次/5分钟
    async def login(username: str, password: str):
        ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 构建速率限制键
            rate_key = f"rate_limit:{scope}:{key}"

            # 确保 Redis 客户端已初始化
            if not redis_client.client:
                await redis_client.init()

            # 增加计数
            count = await redis_client.incr(rate_key)
            if count == 1:
                # 设置过期时间
                if isinstance(period, timedelta):
                    expire_seconds = int(period.total_seconds())
                else:
                    expire_seconds = period
                await redis_client.expire(rate_key, expire_seconds)

            # 检查是否超过限制
            if count > limit:
                raise Exception(f"Rate limit exceeded for {key}")

            # 执行原函数
            return await func(*args, **kwargs)

        return wrapper

    return decorator
