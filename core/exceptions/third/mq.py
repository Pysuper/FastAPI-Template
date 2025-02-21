"""
消息队列服务相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class MessageQueueException(BusinessException):
    """消息队列异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.MESSAGE_SERVICE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化消息队列异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"mq_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class RabbitMQException(MessageQueueException):
    """RabbitMQ异常基类"""

    def __init__(
        self,
        message: str = "RabbitMQ服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"rabbitmq_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class KafkaException(MessageQueueException):
    """Kafka异常基类"""

    def __init__(
        self,
        message: str = "Kafka服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"kafka_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessagePublishException(MessageQueueException):
    """消息发布异常"""

    def __init__(
        self,
        message: str = "消息发布失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"publish_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessageConsumeException(MessageQueueException):
    """消息消费异常"""

    def __init__(
        self,
        message: str = "消息消费失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"consume_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessageAckException(MessageQueueException):
    """消息确认异常"""

    def __init__(
        self,
        message: str = "消息确认失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"ack_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueueDeclareException(MessageQueueException):
    """队列声明异常"""

    def __init__(
        self,
        message: str = "队列声明失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"declare_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExchangeDeclareException(MessageQueueException):
    """交换机声明异常"""

    def __init__(
        self,
        message: str = "交换机声明失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"exchange_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ChannelException(MessageQueueException):
    """通道异常"""

    def __init__(
        self,
        message: str = "通道操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"channel_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 