"""
健康检查相关的业务异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class HealthBusinessException(BusinessException):
    """健康检查业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.BUSINESS_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化健康检查业务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"health_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class ServiceUnavailableException(HealthBusinessException):
    """服务不可用异常"""

    def __init__(
        self,
        message: str = "服务不可用",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"service_unavailable": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DatabaseHealthException(HealthBusinessException):
    """数据库健康检查异常"""

    def __init__(
        self,
        message: str = "数据库连接异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"database_health": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class CacheHealthException(HealthBusinessException):
    """缓存健康检查异常"""

    def __init__(
        self,
        message: str = "缓存服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"cache_health": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class StorageHealthException(HealthBusinessException):
    """存储健康检查异常"""

    def __init__(
        self,
        message: str = "存储服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"storage_health": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DependencyHealthException(HealthBusinessException):
    """依赖服务健康检查异常"""

    def __init__(
        self,
        message: str = "依赖服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"dependency_health": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MetricsException(HealthBusinessException):
    """指标采集异常"""

    def __init__(
        self,
        message: str = "指标采集失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"metrics_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 