"""
缓存相关的业务异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class CacheBusinessException(BusinessException):
    """缓存业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.CACHE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化缓存业务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"cache_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class CacheKeyNotFoundException(CacheBusinessException):
    """缓存键不存在异常"""

    def __init__(
        self,
        message: str = "缓存键不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"key_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class CacheSetException(CacheBusinessException):
    """缓存设置异常"""

    def __init__(
        self,
        message: str = "缓存设置失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"set_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class CacheGetException(CacheBusinessException):
    """缓存获取异常"""

    def __init__(
        self,
        message: str = "缓存获取失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"get_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class CacheDeleteException(CacheBusinessException):
    """缓存删除异常"""

    def __init__(
        self,
        message: str = "缓存删除失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"delete_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class CacheExpiredException(CacheBusinessException):
    """缓存过期异常"""

    def __init__(
        self,
        message: str = "缓存已过期",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"expired": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class CacheConnectionException(CacheBusinessException):
    """缓存连接异常"""

    def __init__(
        self,
        message: str = "缓存连接失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"connection_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class CacheCapacityException(CacheBusinessException):
    """缓存容量异常"""

    def __init__(
        self,
        message: str = "缓存容量不足",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"capacity_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 