"""
异步数据库相关的异常模块
"""

from typing import Dict, Optional

from core.exceptions.system.database import DatabaseException


class AsyncDatabaseException(DatabaseException):
    """异步数据库异常基类"""

    def __init__(
        self,
        message: str = "异步数据库错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化异步数据库异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"async_db_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class GreenletException(AsyncDatabaseException):
    """Greenlet异常"""

    def __init__(
        self,
        message: str = "Greenlet错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化Greenlet异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"greenlet_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AsyncConnectionException(AsyncDatabaseException):
    """异步连接异常"""

    def __init__(
        self,
        message: str = "异步数据库连接失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化异步连接异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"async_connection_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AsyncTransactionException(AsyncDatabaseException):
    """异步事务异常"""

    def __init__(
        self,
        message: str = "异步数据库事务失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化异步事务异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"async_transaction_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AsyncQueryException(AsyncDatabaseException):
    """异步查询异常"""

    def __init__(
        self,
        message: str = "异步数据库查询失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化异步查询异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"async_query_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AsyncSessionException(AsyncDatabaseException):
    """异步会话异常"""

    def __init__(
        self,
        message: str = "异步数据库会话错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化异步会话异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"async_session_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AsyncPoolException(AsyncDatabaseException):
    """异步连接池异常"""

    def __init__(
        self,
        message: str = "异步数据库连接池错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化异步连接池异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"async_pool_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AsyncEngineException(AsyncDatabaseException):
    """异步引擎异常"""

    def __init__(
        self,
        message: str = "异步数据库引擎错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化异步引擎异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"async_engine_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
