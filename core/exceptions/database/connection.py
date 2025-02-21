"""
数据库连接相关的异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class DatabaseConnectionException(BusinessException):
    """数据库连接异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.DATABASE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化数据库连接异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"database_connection_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class ConnectionTimeoutException(DatabaseConnectionException):
    """数据库连接超时异常"""

    def __init__(
        self,
        message: str = "数据库连接超时",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"connection_timeout": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ConnectionPoolExhaustedException(DatabaseConnectionException):
    """连接池耗尽异常"""

    def __init__(
        self,
        message: str = "数据库连接池已耗尽",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"pool_exhausted": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ConnectionClosedException(DatabaseConnectionException):
    """连接已关闭异常"""

    def __init__(
        self,
        message: str = "数据库连接已关闭",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"connection_closed": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ConnectionAuthenticationException(DatabaseConnectionException):
    """连接认证异常"""

    def __init__(
        self,
        message: str = "数据库认证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"authentication_failed": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MaxConnectionsException(DatabaseConnectionException):
    """最大连接数异常"""

    def __init__(
        self,
        message: str = "达到最大连接数限制",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"max_connections": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ConnectionConfigException(DatabaseConnectionException):
    """连接配置异常"""

    def __init__(
        self,
        message: str = "数据库连接配置错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"config_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
