import functools
import time
from typing import Any, Callable, Dict, TypeVar, cast

from fastapi import Request

from core.core.context import get_request_context
from core.core.logic import UnifiedLogger

T = TypeVar("T")
logger = UnifiedLogger("helpers")


def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    """记录函数执行时间的装饰器"""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} executed in {execution_time:.3f} seconds",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "args": args,
                    "kwargs": kwargs,
                },
            )

    return cast(Callable[..., T], wrapper)


def async_log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    """记录异步函数执行时间的装饰器"""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logger.info(
                f"Async function {func.__name__} executed in {execution_time:.3f} seconds",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "args": args,
                    "kwargs": kwargs,
                },
            )

    return cast(Callable[..., T], wrapper)


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    elif "X-Real-IP" in request.headers:
        return request.headers["X-Real-IP"]
    return request.client.host if request.client else ""


def get_request_metadata(request: Request) -> Dict[str, Any]:
    """获取请求元数据"""
    context = get_request_context(request)
    return {
        "request_id": context.request_id,
        "client_ip": get_client_ip(request),
        "user_agent": request.headers.get("user-agent"),
        "referer": request.headers.get("referer"),
        "path": request.url.path,
        "method": request.method,
        "process_time": context.process_time,
    }


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全的JSON解析"""
    try:
        import json

        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON parse error: {str(e)}", extra={"json_str": json_str})
        return default


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串"""
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def format_exception(exc: Exception) -> Dict[str, Any]:
    """格式化异常信息"""
    import traceback

    return {
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
    }
