"""
实时通讯服务相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class RealtimeException(BusinessException):
    """实时通讯异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.THIRD_PARTY_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化实时通讯异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"realtime_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class WebSocketException(RealtimeException):
    """WebSocket异常基类"""

    def __init__(
        self,
        message: str = "WebSocket服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"websocket_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SocketIOException(RealtimeException):
    """Socket.IO异常基类"""

    def __init__(
        self,
        message: str = "Socket.IO服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"socketio_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ConnectionException(RealtimeException):
    """连接异常"""

    def __init__(
        self,
        message: str = "连接失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"connection_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DisconnectException(RealtimeException):
    """断开连接异常"""

    def __init__(
        self,
        message: str = "断开连接失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"disconnect_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessageSendException(RealtimeException):
    """消息发送异常"""

    def __init__(
        self,
        message: str = "消息发送失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"send_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MessageReceiveException(RealtimeException):
    """消息接收异常"""

    def __init__(
        self,
        message: str = "消息接收失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"receive_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class RoomException(RealtimeException):
    """房间操作异常"""

    def __init__(
        self,
        message: str = "房间操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"room_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class EventException(RealtimeException):
    """事件处理异常"""

    def __init__(
        self,
        message: str = "事件处理失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"event_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class HeartbeatException(RealtimeException):
    """心跳异常"""

    def __init__(
        self,
        message: str = "心跳检测失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"heartbeat_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 