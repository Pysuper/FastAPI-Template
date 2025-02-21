"""
API调用相关的业务异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class APIBusinessException(BusinessException):
    """API调用业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.API_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化API调用业务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"api_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class APIRequestException(APIBusinessException):
    """API请求异常"""

    def __init__(
        self,
        message: str = "API请求失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"request_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class APIResponseException(APIBusinessException):
    """API响应异常"""

    def __init__(
        self,
        message: str = "API响应异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"response_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class APITimeoutException(APIBusinessException):
    """API超时异常"""

    def __init__(
        self,
        message: str = "API调用超时",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"timeout_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class APIAuthenticationException(APIBusinessException):
    """API认证异常"""

    def __init__(
        self,
        message: str = "API认证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"authentication_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class APIRateLimitException(APIBusinessException):
    """API限流异常"""

    def __init__(
        self,
        message: str = "API调用频率超限",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"rate_limit_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class APIVersionException(APIBusinessException):
    """API版本异常"""

    def __init__(
        self,
        message: str = "API版本不兼容",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"version_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class APIServiceUnavailableException(APIBusinessException):
    """API服务不可用异常"""

    def __init__(
        self,
        message: str = "API服务不可用",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"service_unavailable": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 