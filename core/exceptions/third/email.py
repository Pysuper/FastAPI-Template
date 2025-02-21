"""
邮件服务相关的异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class EmailException(BusinessException):
    """邮件服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.MESSAGE_SERVICE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化邮件服务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"email_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class EmailSendException(EmailException):
    """邮件发送异常"""

    def __init__(
        self,
        message: str = "邮件发送失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"send_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class EmailTemplateException(EmailException):
    """邮件模板异常"""

    def __init__(
        self,
        message: str = "邮件模板错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"template_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class EmailAttachmentException(EmailException):
    """邮件附件异常"""

    def __init__(
        self,
        message: str = "邮件附件错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"attachment_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class EmailConfigException(EmailException):
    """邮件配置异常"""

    def __init__(
        self,
        message: str = "邮件配置错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"config_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class EmailQuotaException(EmailException):
    """邮件配额异常"""

    def __init__(
        self,
        message: str = "邮件配额超限",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"quota_exceeded": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class EmailAuthenticationException(EmailException):
    """邮件认证异常"""

    def __init__(
        self,
        message: str = "邮件认证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"authentication_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class EmailValidationException(EmailException):
    """邮件验证异常"""

    def __init__(
        self,
        message: str = "邮件格式验证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"validation_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
