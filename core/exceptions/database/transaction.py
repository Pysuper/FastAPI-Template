"""
数据库事务相关的异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class TransactionException(BusinessException):
    """事务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.DATABASE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化事务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"transaction_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class TransactionCommitException(TransactionException):
    """事务提交异常"""

    def __init__(
        self,
        message: str = "事务提交失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"commit_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TransactionRollbackException(TransactionException):
    """事务回滚异常"""

    def __init__(
        self,
        message: str = "事务回滚失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"rollback_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TransactionTimeoutException(TransactionException):
    """事务超时异常"""

    def __init__(
        self,
        message: str = "事务执行超时",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"timeout_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TransactionDeadlockException(TransactionException):
    """事务死锁异常"""

    def __init__(
        self,
        message: str = "事务发生死锁",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"deadlock_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TransactionIsolationException(TransactionException):
    """事务隔离级别异常"""

    def __init__(
        self,
        message: str = "事务隔离级别错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"isolation_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class NestedTransactionException(TransactionException):
    """嵌套事务异常"""

    def __init__(
        self,
        message: str = "嵌套事务错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"nested_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
