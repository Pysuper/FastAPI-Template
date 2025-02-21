"""
支付相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class PaymentBusinessException(BusinessException):
    """支付业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.PAYMENT_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化支付业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"payment_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class PaymentFailedException(PaymentBusinessException):
    """支付失败异常"""

    def __init__(
        self,
        message: str = "支付失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"payment_failed": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentTimeoutException(PaymentBusinessException):
    """支付超时异常"""

    def __init__(
        self,
        message: str = "支付超时",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"payment_timeout": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class InsufficientBalanceException(PaymentBusinessException):
    """余额不足异常"""

    def __init__(
        self,
        message: str = "余额不足",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"insufficient_balance": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentChannelException(PaymentBusinessException):
    """支付渠道异常"""

    def __init__(
        self,
        message: str = "支付渠道异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"channel_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class RefundException(PaymentBusinessException):
    """退款异常"""

    def __init__(
        self,
        message: str = "退款失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"refund_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentVerificationException(PaymentBusinessException):
    """支付验证异常"""

    def __init__(
        self,
        message: str = "支付验证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"verification_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentLimitException(PaymentBusinessException):
    """支付限额异常"""

    def __init__(
        self,
        message: str = "超出支付限额",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"limit_exceeded": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
