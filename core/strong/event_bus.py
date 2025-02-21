"""
事件总线模块
实现异步事件的发布和订阅
"""

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from core.exceptions.system.api import SystemException

logger = logging.getLogger(__name__)


class Event:
    """事件基类"""

    def __init__(self, name: str, data: Any = None):
        self.name = name
        self.data = data
        self.timestamp = asyncio.get_event_loop().time()

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, data={self.data})"


class EventBus:
    """异步事件总线"""

    def __init__(self):
        # 事件处理器映射 {事件名称: {处理器集合}}
        self._handlers: Dict[str, Set[Callable]] = {}
        # 错误处理器
        self._error_handlers: List[Callable] = []
        # 事件处理锁
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        """
        发布事件
        :param event: 事件对象
        """
        handlers = self._handlers.get(event.name, set())
        if not handlers:
            logger.debug(f"No handlers found for event: {event}")
            return

        async with self._lock:
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(self._safe_handle(handler, event))
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_handle(self, handler: Callable, event: Event) -> None:
        """
        安全地执行事件处理器
        :param handler: 处理器函数
        :param event: 事件对象
        """
        try:
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            error = SystemException(
                message=f"Error handling event {event.name}",
                handler=handler.__name__,
                original_error=e,
            )
            await self._handle_error(error)

    async def _handle_error(self, error: Exception) -> None:
        """
        处理错误
        :param error: 错误对象
        """
        if not self._error_handlers:
            logger.error(f"Unhandled event error: {error}")
            return

        for handler in self._error_handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(error)
                else:
                    handler(error)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """
        订阅事件
        :param event_name: 事件名称
        :param handler: 处理器函数
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = set()
        self._handlers[event_name].add(handler)

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """
        取消订阅
        :param event_name: 事件名称
        :param handler: 处理器函数
        """
        if event_name in self._handlers:
            self._handlers[event_name].discard(handler)
            if not self._handlers[event_name]:
                del self._handlers[event_name]

    def add_error_handler(self, handler: Callable) -> None:
        """
        添加错误处理器
        :param handler: 错误处理器函数
        """
        if handler not in self._error_handlers:
            self._error_handlers.append(handler)

    def remove_error_handler(self, handler: Callable) -> None:
        """
        移除错误处理器
        :param handler: 错误处理器函数
        """
        if handler in self._error_handlers:
            self._error_handlers.remove(handler)

    def clear(self) -> None:
        """清除所有订阅和错误处理器"""
        self._handlers.clear()
        self._error_handlers.clear()

    async def wait_for(self, event_name: str, timeout: Optional[float] = None) -> Event:
        """
        等待事件发生
        :param event_name: 事件名称
        :param timeout: 超时时间(秒)
        :return: 事件对象
        """
        future = asyncio.get_event_loop().create_future()

        def _handler(event: Event):
            if not future.done():
                future.set_result(event)

        self.subscribe(event_name, _handler)
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            self.unsubscribe(event_name, _handler)


# 创建默认事件总线实例
event_bus = EventBus()

# 导出
__all__ = ["event_bus", "EventBus", "Event"]
