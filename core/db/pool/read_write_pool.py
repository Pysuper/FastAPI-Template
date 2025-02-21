"""
读写分离连接池
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set

from core.config.setting import get_settings
from core.db.core.manager import DatabaseConfig
from core.db.pool.dynamic_pool import DynamicPool

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()


class ReplicaNode:
    """从节点"""

    def __init__(
        self,
        name: str,
        config: DatabaseConfig,
        weight: int = 1,
        max_lag: int = 5,
    ):
        self.name = name
        self.config = config
        self.weight = weight
        self.max_lag = max_lag
        self.pool: Optional[DynamicPool] = None
        self._lag = 0
        self._available = True

    async def start(self):
        """启动从节点"""
        self.pool = DynamicPool(self.config)
        await self.pool.start()
        logger.info(f"Replica node {self.name} started")

    async def stop(self):
        """停止从节点"""
        if self.pool:
            await self.pool.stop()
            self.pool = None
            logger.info(f"Replica node {self.name} stopped")

    async def check_lag(self) -> int:
        """检查复制延迟"""
        if not self.pool:
            return -1

        try:
            async with self.pool.engine.connect() as conn:
                result = await conn.execute("SHOW SLAVE STATUS")
                row = result.fetchone()
                if row:
                    self._lag = row.Seconds_Behind_Master or 0
                    self._available = True
                    return self._lag
        except Exception as e:
            logger.error(f"Failed to check lag for replica {self.name}", exc_info=e)
            self._available = False
            self._lag = -1

        return self._lag

    @property
    def is_available(self) -> bool:
        """是否可用"""
        return self._available and self._lag <= self.max_lag


class TransactionRouter:
    """事务路由器"""

    def __init__(
        self,
        pool: "ReadWritePool",
        force_master_keywords: Optional[Set[str]] = None,
        force_master_tables: Optional[Set[str]] = None,
        allow_replica_lag: int = 5,
        transaction_route_to_master: bool = True,
    ):
        self.pool = pool
        self.force_master_keywords = force_master_keywords or {"INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"}
        self.force_master_tables = force_master_tables or set()
        self.allow_replica_lag = allow_replica_lag
        self.transaction_route_to_master = transaction_route_to_master

    def should_use_master(self, sql: str, in_transaction: bool = False) -> bool:
        """是否使用主库"""
        # 在事务中且配置为使用主库
        if in_transaction and self.transaction_route_to_master:
            return True

        # 包含强制主库关键字
        sql_upper = sql.upper()
        if any(keyword in sql_upper for keyword in self.force_master_keywords):
            return True

        # 包含强制主库表
        if any(table in sql_upper for table in self.force_master_tables):
            return True

        return False


class ReadWritePool:
    """读写分离连接池"""

    def __init__(
        self,
        master_config: DatabaseConfig,
        replica_configs: List[Dict] = None,
        read_strategy: str = "random",  # random, round_robin, weighted
        auto_failover: bool = True,
        health_check_interval: int = 10,
        force_master_keywords: Optional[set] = None,
        force_master_tables: Optional[set] = None,
        allow_replica_lag: int = 5,
        transaction_route_to_master: bool = True,
        sticky_master: bool = True,
        track_queries: bool = True,
    ):
        self.master_config = master_config
        self.replica_configs = replica_configs or []
        self.read_strategy = read_strategy
        self.auto_failover = auto_failover
        self.health_check_interval = health_check_interval

        # 路由配置
        self.force_master_keywords = force_master_keywords
        self.force_master_tables = force_master_tables
        self.allow_replica_lag = allow_replica_lag
        self.transaction_route_to_master = transaction_route_to_master
        self.sticky_master = sticky_master
        self.track_queries = track_queries

        self.master_pool: Optional[DynamicPool] = None
        self.replicas: List[ReplicaNode] = []
        self._current_replica = 0  # 用于轮询策略
        self._monitor_task = None
        self._router: Optional[TransactionRouter] = None

    async def start(self):
        """启动读写分离池"""
        # 启动主节点
        self.master_pool = DynamicPool(self.master_config)
        await self.master_pool.start()
        logger.info("Master pool started")

        # 启动从节点
        for idx, config in enumerate(self.replica_configs):
            replica = ReplicaNode(
                name=f"replica_{idx}",
                config=DatabaseConfig(**config["config"]),
                weight=config.get("weight", 1),
                max_lag=config.get("max_lag", 5),
            )
            await replica.start()
            self.replicas.append(replica)

        # 创建路由器
        self._router = TransactionRouter(
            pool=self,
            force_master_keywords=self.force_master_keywords,
            force_master_tables=self.force_master_tables,
            allow_replica_lag=self.allow_replica_lag,
            transaction_route_to_master=self.transaction_route_to_master,
        )

        # 启动健康检查
        self._monitor_task = asyncio.create_task(self._health_check())

    async def stop(self):
        """停止读写分离池"""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None

        if self.master_pool:
            await self.master_pool.stop()
            self.master_pool = None

        for replica in self.replicas:
            await replica.stop()
        self.replicas.clear()

    async def _health_check(self):
        """健康检查"""
        while True:
            try:
                # 检查主库
                if self.master_pool:
                    try:
                        async with self.master_pool.engine.connect() as conn:
                            await conn.execute("SELECT 1")
                    except Exception as e:
                        logger.error("Master database health check failed", exc_info=e)

                # 检查从库
                for replica in self.replicas:
                    await replica.check_lag()

            except Exception as e:
                logger.error("Health check failed", exc_info=e)

            await asyncio.sleep(self.health_check_interval)

    def get_read_pool(self) -> Optional[DynamicPool]:
        """获取读连接池"""
        # 如果没有可用的从库，返回主库
        available_replicas = [r for r in self.replicas if r.is_available]
        if not available_replicas:
            return self.master_pool

        # 根据策略选择从库
        if self.read_strategy == "random":
            return available_replicas[0].pool
        elif self.read_strategy == "round_robin":
            self._current_replica = (self._current_replica + 1) % len(available_replicas)
            return available_replicas[self._current_replica].pool
        elif self.read_strategy == "weighted":
            total_weight = sum(r.weight for r in available_replicas)
            if total_weight == 0:
                return available_replicas[0].pool

            # 加权随机
            import random
            r = random.uniform(0, total_weight)
            for replica in available_replicas:
                r -= replica.weight
                if r <= 0:
                    return replica.pool

        return available_replicas[0].pool

    def get_write_pool(self) -> Optional[DynamicPool]:
        """获取写连接池"""
        return self.master_pool

    async def get_status(self) -> Dict[str, dict]:
        """获取连接池状态"""
        status = {
            "master": await self.master_pool.get_status() if self.master_pool else None,
            "replicas": {},
        }

        for replica in self.replicas:
            status["replicas"][replica.name] = {
                "available": replica.is_available,
                "lag": replica._lag,
                "pool": await replica.pool.get_status() if replica.pool else None,
            }

        return status
