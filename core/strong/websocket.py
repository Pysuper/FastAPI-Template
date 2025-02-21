"""
WebSocket管理器
实现WebSocket连接管理和消息广播
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set, Union

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.strong.event_bus import Event, event_bus

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""

    type: str
    data: Any = None
    room: Optional[str] = None
    sender: Optional[str] = None


class WebSocketConnection:
    """WebSocket连接"""

    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.rooms: Set[str] = set()
        self.user_data: Dict[str, Any] = {}

    async def send_json(self, message: Union[dict, WebSocketMessage]) -> None:
        """发送JSON消息"""
        if isinstance(message, WebSocketMessage):
            message = message.dict()
        await self.websocket.send_json(message)

    async def send_text(self, message: str) -> None:
        """发送文本消息"""
        await self.websocket.send_text(message)

    def join_room(self, room: str) -> None:
        """加入房间"""
        self.rooms.add(room)

    def leave_room(self, room: str) -> None:
        """离开房间"""
        self.rooms.discard(room)

    def in_room(self, room: str) -> bool:
        """检查是否在房间中"""
        return room in self.rooms


class WebSocketManager:
    """WebSocket管理器"""

    def __init__(self):
        self._connections: Dict[str, WebSocketConnection] = {}
        self._rooms: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> WebSocketConnection:
        """
        处理WebSocket连接
        :param websocket: WebSocket连接对象
        :param client_id: 客户端ID
        :return: 连接对象
        """
        await websocket.accept()

        async with self._lock:
            connection = WebSocketConnection(websocket, client_id)
            self._connections[client_id] = connection

            # 发布连接事件
            await event_bus.publish(Event("websocket_connected", {"client_id": client_id}))

            return connection

    async def disconnect(self, client_id: str) -> None:
        """
        处理WebSocket断开连接
        :param client_id: 客户端ID
        """
        async with self._lock:
            if client_id in self._connections:
                connection = self._connections[client_id]

                # 离开所有房间
                rooms = list(connection.rooms)
                for room in rooms:
                    await self.leave_room(client_id, room)

                # 删除连接
                del self._connections[client_id]

                # 发布断开连接事件
                await event_bus.publish(Event("websocket_disconnected", {"client_id": client_id}))

    async def broadcast(
        self,
        message: Union[dict, WebSocketMessage],
        room: Optional[str] = None,
        exclude: Optional[Union[str, List[str]]] = None,
    ) -> None:
        """
        广播消息
        :param message: 消息内容
        :param room: 目标房间
        :param exclude: 排除的客户端ID
        """
        if isinstance(exclude, str):
            exclude = [exclude]
        exclude = exclude or []

        if isinstance(message, dict):
            message = WebSocketMessage(**message)

        async with self._lock:
            if room:
                # 向指定房间广播
                if room in self._rooms:
                    for client_id in self._rooms[room]:
                        if client_id not in exclude:
                            await self._send_to_client(client_id, message)
            else:
                # 向所有客户端广播
                for client_id in self._connections:
                    if client_id not in exclude:
                        await self._send_to_client(client_id, message)

    async def _send_to_client(self, client_id: str, message: WebSocketMessage) -> None:
        """
        发送消息给指定客户端
        :param client_id: 客户端ID
        :param message: 消息内容
        """
        if client_id in self._connections:
            try:
                await self._connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                await self.disconnect(client_id)

    async def join_room(self, client_id: str, room: str) -> None:
        """
        加入房间
        :param client_id: 客户端ID
        :param room: 房间名称
        """
        async with self._lock:
            if client_id in self._connections:
                if room not in self._rooms:
                    self._rooms[room] = set()

                self._rooms[room].add(client_id)
                self._connections[client_id].join_room(room)

                # 发布加入房间事件
                await event_bus.publish(
                    Event(
                        "websocket_room_joined",
                        {
                            "client_id": client_id,
                            "room": room,
                        },
                    )
                )

    async def leave_room(self, client_id: str, room: str) -> None:
        """
        离开房间
        :param client_id: 客户端ID
        :param room: 房间名称
        """
        async with self._lock:
            if room in self._rooms and client_id in self._rooms[room]:
                self._rooms[room].remove(client_id)

                # 如果房间为空，删除房间
                if not self._rooms[room]:
                    del self._rooms[room]

                if client_id in self._connections:
                    self._connections[client_id].leave_room(room)

                # 发布离开房间事件
                await event_bus.publish(
                    Event(
                        "websocket_room_left",
                        {
                            "client_id": client_id,
                            "room": room,
                        },
                    )
                )

    def get_connection(self, client_id: str) -> Optional[WebSocketConnection]:
        """获取连接对象"""
        return self._connections.get(client_id)

    def get_connections(self) -> List[WebSocketConnection]:
        """获取所有连接"""
        return list(self._connections.values())

    def get_room_connections(self, room: str) -> List[WebSocketConnection]:
        """获取房间内的所有连接"""
        if room not in self._rooms:
            return []
        return [conn for conn in self._connections.values() if conn.client_id in self._rooms[room]]

    def get_rooms(self) -> List[str]:
        """获取所有房间"""
        return list(self._rooms.keys())

    async def handle_connection(self, websocket: WebSocket, client_id: str) -> None:
        """
        处理WebSocket连接的主循环
        :param websocket: WebSocket连接对象
        :param client_id: 客户端ID
        """
        connection = await self.connect(websocket, client_id)

        try:
            while True:
                try:
                    # 接收消息
                    data = await websocket.receive_json()
                    message = WebSocketMessage(
                        type=data.get("type", "message"),
                        data=data.get("data"),
                        room=data.get("room"),
                        sender=client_id,
                    )

                    # 发布消息接收事件
                    await event_bus.publish(Event("websocket_message_received", message))

                    # 处理房间消息
                    if message.room:
                        await self.broadcast(message, room=message.room, exclude=client_id)

                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON message from client {client_id}")
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {e}")

        finally:
            await self.disconnect(client_id)


# 创建默认WebSocket管理器实例
websocket_manager = WebSocketManager()

# 导出
__all__ = [
    "websocket_manager",
    "WebSocketManager",
    "WebSocketConnection",
    "WebSocketMessage",
]
