"""
系统管理相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class SystemBusinessException(BusinessException):
    """系统管理业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.SYSTEM_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化系统管理业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"system_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class ConfigurationException(SystemBusinessException):
    """配置异常"""

    def __init__(
        self,
        message: str = "系统配置错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"config_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MaintenanceModeException(SystemBusinessException):
    """维护模式异常"""

    def __init__(
        self,
        message: str = "系统维护中",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"maintenance_mode": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ResourceExhaustedException(SystemBusinessException):
    """资源耗尽异常"""

    def __init__(
        self,
        message: str = "系统资源不足",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"resource_exhausted": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class BackupException(SystemBusinessException):
    """备份异常"""

    def __init__(
        self,
        message: str = "系统备份失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"backup_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class RestoreException(SystemBusinessException):
    """恢复异常"""

    def __init__(
        self,
        message: str = "系统恢复失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"restore_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class VersionConflictException(SystemBusinessException):
    """版本冲突异常"""

    def __init__(
        self,
        message: str = "系统版本冲突",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"version_conflict": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SystemOverloadException(SystemBusinessException):
    """系统过载异常"""

    def __init__(
        self,
        message: str = "系统负载过高",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"system_overload": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
