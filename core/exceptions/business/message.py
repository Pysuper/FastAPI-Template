"""
消息通知相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class MessageBusinessException(BusinessException):
    """消息通知业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.BUSINESS_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化消息通知业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"message_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class MessageNotFoundException(MessageBusinessException):
    """消息不存在异常"""

    def __init__(
        self,
        message: str = "消息不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"message_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessageSendException(MessageBusinessException):
    """消息发送异常"""

    def __init__(
        self,
        message: str = "消息发送失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"message_send_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessageTemplateException(MessageBusinessException):
    """消息模板异常"""

    def __init__(
        self,
        message: str = "消息模板错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"template_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessageQuotaException(MessageBusinessException):
    """消息配额异常"""

    def __init__(
        self,
        message: str = "消息配额超限",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"quota_exceeded": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessageChannelException(MessageBusinessException):
    """消息渠道异常"""

    def __init__(
        self,
        message: str = "消息渠道错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"channel_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
