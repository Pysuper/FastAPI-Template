"""
数据库相关的系统异常模块
"""

from typing import Any, Dict, Optional

from core.exceptions.base.base_exception import BaseException
from core.exceptions.base.error_codes import ErrorCode


class DatabaseException(BaseException):
    """数据库异常基类"""

    def __init__(
        self,
        message: str = "数据库错误",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化数据库异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            details=details,
            context=context,
        )


class SessionException(DatabaseException):
    """数据库会话异常"""

    def __init__(
        self,
        message: str = "数据库会话错误",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化数据库会话异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"session_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ConnectionException(DatabaseException):
    """数据库连接异常"""

    def __init__(
        self,
        message: str = "数据库连接失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化数据库连接异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"connection_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryException(DatabaseException):
    """数据库查询异常"""

    def __init__(
        self,
        message: str = "数据库查询失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化数据库查询异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"query_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TransactionException(DatabaseException):
    """数据库事务异常"""

    def __init__(
        self,
        message: str = "数据库事务失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化数据库事务异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"transaction_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MigrationException(DatabaseException):
    """数据库迁移异常"""

    def __init__(
        self,
        message: str = "数据库迁移失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化数据库迁移异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"migration_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
