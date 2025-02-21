"""
监控异常模块
"""
from typing import Any, Dict, Optional


class MonitorError(Exception):
    """监控异常基类"""

    def __init__(
        self,
        message: str,
        code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.code = code or 500
        self.details = details or {}
        super().__init__(message)


class MonitorConfigError(MonitorError):
    """监控配置异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=400, details=details)


class MonitorConnectionError(MonitorError):
    """监控连接异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=503, details=details)


class MonitorTimeoutError(MonitorError):
    """监控超时异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=504, details=details)


class MonitorRateLimitError(MonitorError):
    """监控限流异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=429, details=details)


class MonitorCircuitBreakerError(MonitorError):
    """监控熔断异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=503, details=details)


class MonitorRetryError(MonitorError):
    """监控重试异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=503, details=details)


class MonitorQueryError(MonitorError):
    """监控查询异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=500, details=details)


class MonitorCacheError(MonitorError):
    """监控缓存异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=500, details=details)


class MonitorTransactionError(MonitorError):
    """监控事务异常"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=500, details=details) 