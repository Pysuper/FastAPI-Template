"""
异常处理装饰器模块
"""

import asyncio
import functools
import logging
import time
import traceback
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.http.validation import ValidationException
from core.exceptions.system.api import BusinessException

logger = logging.getLogger(__name__)

T = TypeVar("T")


def handle_exceptions(
    *exceptions: Type[Exception],
    reraise: bool = False,
    log_level: int = logging.ERROR,
    error_code: Optional[ErrorCode] = None,
    error_message: Optional[str] = None,
) -> Callable:
    """
    异常处理装饰器

    Args:
        exceptions: 要处理的异常类型
        reraise: 是否重新抛出异常
        log_level: 日志级别
        error_code: 错误码
        error_message: 错误信息

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except exceptions as exc:
                _handle_exception(exc, func, log_level, error_code, error_message)
                if reraise:
                    raise
                return None

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except exceptions as exc:
                _handle_exception(exc, func, log_level, error_code, error_message)
                if reraise:
                    raise
                return None

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def _handle_exception(
    exc: Exception,
    func: Callable,
    log_level: int,
    error_code: Optional[ErrorCode],
    error_message: Optional[str],
) -> None:
    """
    处理异常

    Args:
        exc: 异常对象
        func: 原始函数
        log_level: 日志级别
        error_code: 错误码
        error_message: 错误信息
    """
    # 获取异常信息
    exc_info = {
        "function": f"{func.__module__}.{func.__name__}",
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
    }

    # 记录日志
    logger.log(
        log_level,
        f"Exception in {exc_info['function']}: {exc_info['error_message']}",
        extra=exc_info,
        exc_info=True,
    )

    # 如果需要，转换为业务异常
    if error_code:
        raise BusinessException(
            message=error_message or str(exc),
            code=error_code,
            details=exc_info,
        )


def wrap_exceptions(
    target_exc: Type[BusinessException],
    *source_excs: Type[Exception],
    message: Optional[str] = None,
    include_context: bool = True,
) -> Callable:
    """
    异常转换装饰器

    Args:
        target_exc: 目标异常类型
        source_excs: 源异常类型
        message: 错误信息
        include_context: 是否包含上下文信息

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except source_excs as exc:
                details = {"original_error": str(exc)}
                if include_context:
                    details.update(
                        {
                            "function": f"{func.__module__}.{func.__name__}",
                            "args": args,
                            "kwargs": kwargs,
                        }
                    )
                raise target_exc(message=message or str(exc), details=details) from exc

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except source_excs as exc:
                details = {"original_error": str(exc)}
                if include_context:
                    details.update(
                        {
                            "function": f"{func.__module__}.{func.__name__}",
                            "args": args,
                            "kwargs": kwargs,
                        }
                    )
                raise target_exc(message=message or str(exc), details=details) from exc

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def validate_or_raise(
    condition: bool,
    message: str,
    code: ErrorCode = ErrorCode.VALIDATION_ERROR,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    验证条件，不满足则抛出异常

    Args:
        condition: 验证条件
        message: 错误信息
        code: 错误码
        details: 错误详情
    """
    if not condition:
        raise ValidationException(message=message, details=details)


def ensure_not_none(
    value: Optional[T],
    message: str = "值不能为空",
    details: Optional[Dict[str, Any]] = None,
) -> T:
    """
    确保值不为None

    Args:
        value: 要检查的值
        message: 错误信息
        details: 错误详情

    Returns:
        非None的值
    """
    if value is None:
        raise ValidationException(message=message, details=details)
    return value


def retry_on_exception(
    *exceptions: Type[Exception],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    logger: Optional[logging.Logger] = None,
) -> Callable:
    """
    异常重试装饰器

    Args:
        exceptions: 要重试的异常类型
        max_attempts: 最大重试次数
        delay: 初始延迟时间(秒)
        backoff: 延迟时间的增长因子
        logger: 日志记录器

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts - 1:
                        raise
                    if logger:
                        logger.warning(f"第{attempt + 1}/{max_attempts}次尝试失败: {str(exc)}")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts - 1:
                        raise
                    if logger:
                        logger.warning(f"第{attempt + 1}/{max_attempts}次尝试失败: {str(exc)}")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
