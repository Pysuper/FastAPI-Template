import asyncio
import random
import socket
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import consul
import etcd3
import py_eureka_client.eureka_client as eureka_client
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger

logger = get_logger("service_discovery")


class ServiceDiscoveryProvider(str, Enum):
    """服务发现提供者"""

    CONSUL = "consul"
    ETCD = "etcd"
    EUREKA = "eureka"


class LoadBalanceStrategy(str, Enum):
    """负载均衡策略"""

    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    LEAST_CONN = "least_conn"
    WEIGHTED = "weighted"


class ServiceInstance:
    """服务实例"""

    def __init__(
        self,
        host: str,
        port: int,
        metadata: Dict[str, Any] = None,
        weight: int = 1,
        healthy: bool = True,
        last_check: datetime = None,
    ):
        self.host = host
        self.port = port
        self.metadata = metadata or {}
        self.weight = weight
        self.healthy = healthy
        self.last_check = last_check or datetime.now()
        self.connection_count = 0


class ServiceDiscovery:
    """服务发现"""

    def __init__(self):
        self.provider = settings.SERVICE_DISCOVERY_PROVIDER
        self._client = None
        self._instances: Dict[str, List[ServiceInstance]] = {}
        self._current_index = 0

    async def init_discovery(self):
        """初始化服务发现"""
        if self.provider == ServiceDiscoveryProvider.CONSUL:
            self._client = consul.Consul(host=settings.SERVICE_DISCOVERY_HOST, port=settings.SERVICE_DISCOVERY_PORT)
        elif self.provider == ServiceDiscoveryProvider.ETCD:
            self._client = etcd3.client(host=settings.SERVICE_DISCOVERY_HOST, port=settings.SERVICE_DISCOVERY_PORT)
        elif self.provider == ServiceDiscoveryProvider.EUREKA:
            self._client = await eureka_client.init_async(
                eureka_server=f"http://{settings.SERVICE_DISCOVERY_HOST}:{settings.SERVICE_DISCOVERY_PORT}/eureka",
                app_name=settings.SERVICE_NAME,
                instance_port=settings.PORT,
            )
        else:
            raise ValueError(f"Unsupported service discovery provider: {self.provider}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def register_service(self):
        """注册服务"""
        try:
            service_id = f"{settings.SERVICE_NAME}-{socket.gethostname()}"

            if self.provider == ServiceDiscoveryProvider.CONSUL:
                self._client.agent.service.register(
                    name=settings.SERVICE_NAME,
                    service_id=service_id,
                    address=socket.gethostname(),
                    port=settings.PORT,
                    tags=settings.SERVICE_TAGS,
                    check={
                        "http": f"http://{socket.gethostname()}:{settings.PORT}/health",
                        "interval": settings.SERVICE_CHECK_INTERVAL,
                        "timeout": settings.SERVICE_CHECK_TIMEOUT,
                        "deregister_critical_service_after": settings.SERVICE_CHECK_DEREGISTER_AFTER,
                    },
                )
            elif self.provider == ServiceDiscoveryProvider.ETCD:
                lease = self._client.lease(ttl=60)
                key = f"/services/{settings.SERVICE_NAME}/{service_id}"
                value = {
                    "name": settings.SERVICE_NAME,
                    "id": service_id,
                    "address": socket.gethostname(),
                    "port": settings.PORT,
                    "tags": settings.SERVICE_TAGS,
                }
                self._client.put(key, str(value), lease=lease)
            elif self.provider == ServiceDiscoveryProvider.EUREKA:
                # Eureka客户端已在初始化时自动注册
                pass

            logger.info(f"Service registered: {service_id}")
        except Exception as e:
            logger.error(f"Failed to register service: {str(e)}")
            raise

    async def deregister_service(self):
        """注销服务"""
        try:
            service_id = f"{settings.SERVICE_NAME}-{socket.gethostname()}"

            if self.provider == ServiceDiscoveryProvider.CONSUL:
                self._client.agent.service.deregister(service_id)
            elif self.provider == ServiceDiscoveryProvider.ETCD:
                key = f"/services/{settings.SERVICE_NAME}/{service_id}"
                self._client.delete(key)
            elif self.provider == ServiceDiscoveryProvider.EUREKA:
                await self._client.stop()

            logger.info(f"Service deregistered: {service_id}")
        except Exception as e:
            logger.error(f"Failed to deregister service: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def discover_service(
        self, service_name: str, strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    ) -> Optional[ServiceInstance]:
        """发现服务"""
        try:
            # 获取服务实例列表
            instances = await self._get_service_instances(service_name)
            if not instances:
                return None

            # 根据负载均衡策略选择实例
            if strategy == LoadBalanceStrategy.RANDOM:
                instance = random.choice(instances)
            elif strategy == LoadBalanceStrategy.ROUND_ROBIN:
                instance = instances[self._current_index % len(instances)]
                self._current_index += 1
            elif strategy == LoadBalanceStrategy.LEAST_CONN:
                instance = min(instances, key=lambda x: x.connection_count)
            elif strategy == LoadBalanceStrategy.WEIGHTED:
                total_weight = sum(instance.weight for instance in instances)
                r = random.uniform(0, total_weight)
                for instance in instances:
                    r -= instance.weight
                    if r <= 0:
                        break
            else:
                raise ValueError(f"Unsupported load balance strategy: {strategy}")

            # 更新连接计数
            instance.connection_count += 1
            return instance

        except Exception as e:
            logger.error(f"Failed to discover service {service_name}: {str(e)}")
            raise

    async def _get_service_instances(self, service_name: str) -> List[ServiceInstance]:
        """获取服务实例列表"""
        instances = []

        try:
            if self.provider == ServiceDiscoveryProvider.CONSUL:
                _, services = self._client.health.service(service_name)
                for service in services:
                    if service["Checks"][0]["Status"] == "passing":
                        instances.append(
                            ServiceInstance(
                                host=service["Service"]["Address"],
                                port=service["Service"]["Port"],
                                metadata=service["Service"]["Meta"],
                                healthy=True,
                                last_check=datetime.now(),
                            )
                        )

            elif self.provider == ServiceDiscoveryProvider.ETCD:
                response = self._client.get_prefix(f"/services/{service_name}/")
                for value, _ in response:
                    service_data = eval(value.decode("utf-8"))
                    instances.append(
                        ServiceInstance(
                            host=service_data["address"],
                            port=service_data["port"],
                            metadata={"tags": service_data["tags"]},
                            healthy=True,
                            last_check=datetime.now(),
                        )
                    )

            elif self.provider == ServiceDiscoveryProvider.EUREKA:
                application = await self._client.get_application(service_name)
                if application:
                    for instance in application.instances:
                        if instance.status == "UP":
                            instances.append(
                                ServiceInstance(
                                    host=instance.ipAddr,
                                    port=instance.port.port,
                                    metadata=instance.metadata,
                                    healthy=True,
                                    last_check=datetime.now(),
                                )
                            )

        except Exception as e:
            logger.error(f"Failed to get service instances for {service_name}: {str(e)}")
            return []

        return instances

    async def watch_service(self, service_name: str, callback):
        """监听服务变化"""
        if self.provider == ServiceDiscoveryProvider.CONSUL:
            index = None
            while True:
                try:
                    index, data = self._client.health.service(service_name, index=index, wait="30s")
                    instances = []
                    for service in data:
                        if service["Checks"][0]["Status"] == "passing":
                            instances.append(
                                ServiceInstance(
                                    host=service["Service"]["Address"],
                                    port=service["Service"]["Port"],
                                    metadata=service["Service"]["Meta"],
                                    healthy=True,
                                    last_check=datetime.now(),
                                )
                            )
                    await callback(instances)
                except Exception as e:
                    logger.error(f"Service watch error: {str(e)}")
                    await asyncio.sleep(5)

        elif self.provider == ServiceDiscoveryProvider.ETCD:
            events_iterator, cancel = self._client.watch_prefix(f"/services/{service_name}/")
            try:
                async for event in events_iterator:
                    instances = await self._get_service_instances(service_name)
                    await callback(instances)
            except Exception as e:
                logger.error(f"Service watch error: {str(e)}")
            finally:
                cancel()

        elif self.provider == ServiceDiscoveryProvider.EUREKA:
            # Eureka客户端自动处理服务发现和健康检查
            pass


# 创建全局服务发现实例
service_discovery = ServiceDiscovery()
