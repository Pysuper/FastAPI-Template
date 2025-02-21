"""
服务发现模块
实现服务的注册、发现和健康检查
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from core.strong.event_bus import Event, event_bus

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态"""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceEndpoint:
    """服务端点"""

    host: str
    port: int
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"


@dataclass
class ServiceInstance:
    """服务实例"""

    id: str
    name: str
    endpoint: ServiceEndpoint
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_heartbeat: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转���为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "endpoint": {
                "host": self.endpoint.host,
                "port": self.endpoint.port,
                "metadata": self.endpoint.metadata,
            },
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceInstance":
        """从字典创建实例"""
        endpoint = ServiceEndpoint(
            host=data["endpoint"]["host"],
            port=data["endpoint"]["port"],
            metadata=data["endpoint"]["metadata"],
        )
        return cls(
            id=data["id"],
            name=data["name"],
            endpoint=endpoint,
            status=ServiceStatus(data["status"]),
            last_heartbeat=data["last_heartbeat"],
            metadata=data["metadata"],
        )


class ServiceRegistry:
    """服务注册中心"""

    def __init__(self, heartbeat_interval: int = 30, heartbeat_timeout: int = 90):
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self._services: Dict[str, Dict[str, ServiceInstance]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """启动服务注册中心"""
        # 从Redis恢复服务实例
        await self._restore_from_redis()

        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """停止服务注册中心"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def register(self, instance: ServiceInstance) -> None:
        """
        注册服务实例
        :param instance: 服务实例
        """
        async with self._lock:
            if instance.name not in self._services:
                self._services[instance.name] = {}

            instance.status = ServiceStatus.STARTING
            self._services[instance.name][instance.id] = instance

            # 保存到Redis
            await self._save_to_redis(instance)

            # 发布服务注册事件
            await event_bus.publish(Event("service_registered", instance.to_dict()))

    async def deregister(self, service_name: str, instance_id: str) -> None:
        """
        注销服务实例
        :param service_name: 服务名称
        :param instance_id: 实例ID
        """
        async with self._lock:
            if service_name in self._services and instance_id in self._services[service_name]:
                instance = self._services[service_name][instance_id]
                instance.status = ServiceStatus.STOPPING

                # 从Redis删除
                await self._remove_from_redis(instance)

                # 删除实例
                del self._services[service_name][instance_id]
                if not self._services[service_name]:
                    del self._services[service_name]

                # 发布服务注销事件
                await event_bus.publish(Event("service_deregistered", instance.to_dict()))

    async def heartbeat(self, service_name: str, instance_id: str) -> None:
        """
        服务心跳
        :param service_name: 服务名称
        :param instance_id: 实例ID
        """
        async with self._lock:
            if service_name in self._services and instance_id in self._services[service_name]:
                instance = self._services[service_name][instance_id]
                instance.last_heartbeat = time.time()
                instance.status = ServiceStatus.HEALTHY

                # 更新Redis
                await self._save_to_redis(instance)

    async def get_service(self, service_name: str) -> List[ServiceInstance]:
        """
        获取服务实例列表
        :param service_name: 服务名称
        :return: 服务实例列表
        """
        if service_name not in self._services:
            return []
        return list(self._services[service_name].values())

    async def get_instance(self, service_name: str, instance_id: str) -> Optional[ServiceInstance]:
        """
        获取服务实例
        :param service_name: 服务名称
        :param instance_id: 实例ID
        :return: 服务实例
        """
        if service_name not in self._services:
            return None
        return self._services[service_name].get(instance_id)

    async def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """
        获取健康的服务实例列表
        :param service_name: 服务名称
        :return: 健康的服务实例列表
        """
        if service_name not in self._services:
            return []
        return [
            instance for instance in self._services[service_name].values() if instance.status == ServiceStatus.HEALTHY
        ]

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._cleanup_expired_instances()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_expired_instances(self) -> None:
        """清理过期的服务实例"""
        now = time.time()
        expired_instances = []

        async with self._lock:
            for service_name, instances in self._services.items():
                for instance_id, instance in instances.items():
                    if now - instance.last_heartbeat > self.heartbeat_timeout:
                        expired_instances.append((service_name, instance_id))

            for service_name, instance_id in expired_instances:
                await self.deregister(service_name, instance_id)

    async def _save_to_redis(self, instance: ServiceInstance) -> None:
        """保存服务实例到Redis"""
        key = f"service:{instance.name}:{instance.id}"
        await redis_cache.set(key, json.dumps(instance.to_dict()))

    async def _remove_from_redis(self, instance: ServiceInstance) -> None:
        """从Redis删除服务实例"""
        key = f"service:{instance.name}:{instance.id}"
        await redis_cache.delete(key)

    async def _restore_from_redis(self) -> None:
        """从Redis恢复服务实例"""
        async with self._lock:
            # 获取所有服务实例键
            keys = await redis_cache.keys("service:*")

            for key in keys:
                try:
                    data = await redis_cache.get(key)
                    if data:
                        instance_data = json.loads(data)
                        instance = ServiceInstance.from_dict(instance_data)

                        if instance.name not in self._services:
                            self._services[instance.name] = {}

                        self._services[instance.name][instance.id] = instance

                except Exception as e:
                    logger.error(f"Error restoring service instance from Redis: {e}")


# 创建默认服务注册中心实例
service_registry = ServiceRegistry()

# 导出
__all__ = [
    "service_registry",
    "ServiceRegistry",
    "ServiceInstance",
    "ServiceEndpoint",
    "ServiceStatus",
]
