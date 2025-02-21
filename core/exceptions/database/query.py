"""
数据库查询相关的异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class QueryException(BusinessException):
    """查询异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.DATABASE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化查询异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"query_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class QuerySyntaxException(QueryException):
    """查询语法异常"""

    def __init__(
        self,
        message: str = "SQL语法错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"syntax_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryTimeoutException(QueryException):
    """查询超时异常"""

    def __init__(
        self,
        message: str = "查询执行超时",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"timeout_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryResultException(QueryException):
    """查询结果异常"""

    def __init__(
        self,
        message: str = "查询结果错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"result_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryParameterException(QueryException):
    """查询参数异常"""

    def __init__(
        self,
        message: str = "查询参数错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"parameter_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryExecutionException(QueryException):
    """查询执行异常"""

    def __init__(
        self,
        message: str = "查询执行失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"execution_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryOptimizationException(QueryException):
    """查询优化异常"""

    def __init__(
        self,
        message: str = "查询优化失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"optimization_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryLockException(QueryException):
    """查询锁异常"""

    def __init__(
        self,
        message: str = "查询锁定失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"lock_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
