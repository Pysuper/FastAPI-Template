"""
缓存相关的系统异常模块
"""

from typing import Any, Dict, Optional

from core.exceptions.base.base_exception import BaseException
from core.exceptions.base.error_codes import ErrorCode


class CacheException(BaseException):
    """缓存异常基类"""

    def __init__(
        self,
        message: str = "缓存错误",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化缓存异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=ErrorCode.CACHE_ERROR,
            message=message,
            details=details,
            context=context,
        )


class RedisException(CacheException):
    """Redis异常"""

    def __init__(
        self,
        message: str = "Redis操作失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化Redis异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"redis_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MemcacheException(CacheException):
    """Memcache异常"""

    def __init__(
        self,
        message: str = "Memcache操作失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化Memcache异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"memcache_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class LocalCacheException(CacheException):
    """本地缓存异常"""

    def __init__(
        self,
        message: str = "本地缓存操作失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化本地缓存异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"local_cache_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class CacheKeyException(CacheException):
    """缓存键异常"""

    def __init__(
        self,
        message: str = "缓存键错误",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化缓存键异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"cache_key_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
