"""
短信服务相关的异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class SMSException(BusinessException):
    """短信服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.MESSAGE_SERVICE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化短信服务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"sms_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class SMSSendException(SMSException):
    """短信发送异常"""

    def __init__(
        self,
        message: str = "短信发送失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"send_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SMSTemplateException(SMSException):
    """短信模板异常"""

    def __init__(
        self,
        message: str = "短信模板错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"template_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SMSConfigException(SMSException):
    """短信配置异常"""

    def __init__(
        self,
        message: str = "短信配置错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"config_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SMSQuotaException(SMSException):
    """短信配额异常"""

    def __init__(
        self,
        message: str = "短信配额超限",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"quota_exceeded": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SMSAuthenticationException(SMSException):
    """短信认证异常"""

    def __init__(
        self,
        message: str = "短信认证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"authentication_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SMSValidationException(SMSException):
    """短信验证异常"""

    def __init__(
        self,
        message: str = "短信格式验证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"validation_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SMSProviderException(SMSException):
    """短信服务商异常"""

    def __init__(
        self,
        message: str = "短信服务商错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"provider_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
