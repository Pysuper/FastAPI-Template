"""
支付服务相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class PaymentServiceException(BusinessException):
    """支付服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.PAYMENT_SERVICE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化支付服务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"payment_service_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class AlipayException(PaymentServiceException):
    """支付宝异常基类"""

    def __init__(
        self,
        message: str = "支付宝服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"alipay_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class WeChatPayException(PaymentServiceException):
    """微信支付异常基类"""

    def __init__(
        self,
        message: str = "微信支付服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"wechat_pay_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentSignException(PaymentServiceException):
    """支付签名异常"""

    def __init__(
        self,
        message: str = "支付签名验证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"sign_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentNotifyException(PaymentServiceException):
    """支付回调异常"""

    def __init__(
        self,
        message: str = "支付回调处理失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"notify_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentRefundException(PaymentServiceException):
    """支付退款异常"""

    def __init__(
        self,
        message: str = "支付退款失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"refund_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentQueryException(PaymentServiceException):
    """支付查询异常"""

    def __init__(
        self,
        message: str = "支付查询失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"query_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentCancelException(PaymentServiceException):
    """支付取消异常"""

    def __init__(
        self,
        message: str = "支付取消失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"cancel_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PaymentTimeoutException(PaymentServiceException):
    """支付超时异常"""

    def __init__(
        self,
        message: str = "支付超时",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"timeout_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 