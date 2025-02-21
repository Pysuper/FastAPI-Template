"""
数据库连接池工厂
"""

import logging
from typing import Dict, Optional

from core.config.setting import get_settings
from core.config.load.db import DatabaseConfig
from core.db.pool.dynamic_pool import DynamicPool
from core.db.pool.read_write_pool import ReadWritePool

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()


class PoolFactory:
    """连接池工厂"""

    def __init__(self):
        self._pools: Dict[str, DynamicPool | ReadWritePool] = {}

    async def create_pool(
        self,
        name: str,
        config: DatabaseConfig,
        pool_type: str = "dynamic",  # dynamic, read_write
        replica_configs: Optional[list] = None,
        read_strategy: str = "random",
        auto_failover: bool = True,
    ) -> DynamicPool | ReadWritePool:
        """创建连接池"""
        if name in self._pools:
            raise ValueError(f"Pool {name} already exists")

        if pool_type == "dynamic":
            pool = DynamicPool(config)
            await pool.start()
            self._pools[name] = pool
            logger.info(f"Created dynamic pool: {name}")
            return pool

        elif pool_type == "read_write":
            if not replica_configs:
                raise ValueError("replica_configs is required for read_write pool")

            pool = ReadWritePool(
                master_config=config,
                replica_configs=replica_configs,
                read_strategy=read_strategy,
                auto_failover=auto_failover,
            )
            await pool.start()
            self._pools[name] = pool
            logger.info(f"Created read_write pool: {name}")
            return pool

        else:
            raise ValueError(f"Unknown pool type: {pool_type}")

    async def get_pool(
        self,
        name: str,
        for_read: bool = False,
    ) -> Optional[DynamicPool]:
        """获取连接池"""
        pool = self._pools.get(name)
        if not pool:
            return None

        if isinstance(pool, ReadWritePool):
            return pool.get_read_pool() if for_read else pool.get_write_pool()
        return pool

    async def close_pool(self, name: str) -> None:
        """关闭连接池"""
        if pool := self._pools.get(name):
            await pool.stop()
            del self._pools[name]
            logger.info(f"Closed pool: {name}")

    async def close_all(self) -> None:
        """关闭所有连接池"""
        for name in list(self._pools.keys()):
            await self.close_pool(name)
        logger.info("All pools closed")

    def get_metrics(self) -> Dict[str, dict]:
        """获取所有连接池指标"""
        metrics = {}
        for name, pool in self._pools.items():
            if isinstance(pool, ReadWritePool):
                metrics[name] = {
                    "type": "read_write",
                    "master": pool.master_pool.metrics.__dict__ if pool.master_pool else None,
                    "replicas": {
                        replica.name: replica.pool.metrics.__dict__ if replica.pool else None
                        for replica in pool.replicas
                    },
                }
            else:
                metrics[name] = {
                    "type": "dynamic",
                    "metrics": pool.metrics.__dict__,
                }
        return metrics


# 全局连接池工厂实例
pool_factory = PoolFactory()

# 导出
__all__ = ["pool_factory", "PoolFactory"]
