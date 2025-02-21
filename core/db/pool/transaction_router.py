import logging
import re
from typing import Optional, Set, Dict

from sqlalchemy.sql import Select, Insert, Update, Delete
from sqlalchemy.sql.elements import ClauseElement

from core.db.pool.dynamic_pool import DynamicPool
from core.db.pool.read_write_pool import ReadWritePool

logger = logging.getLogger(__name__)


class TransactionRouter:
    """事务路由器"""

    # 写操作SQL关键字
    WRITE_KEYWORDS = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE",
        "DROP",
        "ALTER",
        "GRANT",
        "TRUNCATE",
        "REPLACE",
        "LOCK",
    }

    def __init__(
        self,
        pool: ReadWritePool,
        force_master_keywords: Set[str] = None,  # 强制主库关键字
        force_master_tables: Set[str] = None,  # 强制主库表
        allow_replica_lag: int = 5,  # 允许的从库延迟（秒）
        transaction_route_to_master: bool = True,  # 事务是否强制路由到主库
    ):
        self.pool = pool
        self.force_master_keywords = force_master_keywords or set()
        self.force_master_tables = force_master_tables or set()
        self.allow_replica_lag = allow_replica_lag
        self.transaction_route_to_master = transaction_route_to_master

        # SQL解析缓存
        self._parse_cache: Dict[str, bool] = {}

    def is_write_operation(self, sql: str) -> bool:
        """判断是否为写操作"""
        # 检查缓存
        if sql in self._parse_cache:
            return self._parse_cache[sql]

        # 转换为大写以便匹配
        sql_upper = sql.upper()

        # 检查是否包含写操作关键字
        is_write = any(keyword in sql_upper for keyword in self.WRITE_KEYWORDS)

        # 检查是否包含强制主库关键字
        is_force_master = any(keyword in sql_upper for keyword in self.force_master_keywords)

        # 检查是否操作强制主库表
        for table in self.force_master_tables:
            if re.search(rf"\b{table}\b", sql, re.IGNORECASE):
                is_force_master = True
                break

        result = is_write or is_force_master

        # 缓存结果
        self._parse_cache[sql] = result

        return result

    def is_write_statement(self, statement: ClauseElement) -> bool:
        """判断SQLAlchemy语句是否为写操作"""
        return isinstance(statement, (Insert, Update, Delete)) or not isinstance(statement, Select)

    def get_pool_for_statement(
        self,
        statement: Optional[ClauseElement] = None,
        sql: Optional[str] = None,
        in_transaction: bool = False,
    ) -> DynamicPool:
        """获取语句对应的连接池
        Args:
            statement: SQLAlchemy语句
            sql: 原始SQL
            in_transaction: 是否在事务中
        """
        # 在事务中且配置要求路由到主库
        if in_transaction and self.transaction_route_to_master:
            return self.pool.get_write_pool()

        # 判断是否为写操作
        is_write = False

        if statement is not None:
            is_write = self.is_write_statement(statement)
        elif sql is not None:
            is_write = self.is_write_operation(sql)

        # 获取对应的连接池
        if is_write:
            return self.pool.get_write_pool()
        else:
            return self.pool.get_read_pool()

    async def get_suitable_replica(self, required_lag: Optional[int] = None) -> Optional[DynamicPool]:
        """获取满足复制延迟要求的从库
        Args:
            required_lag: 要求的最大复制延���（秒）
        """
        max_lag = required_lag or self.allow_replica_lag

        # 获取所有可用且复制延迟在允许范围内的从库
        suitable_replicas = [
            replica for replica in self.pool.replicas if (replica.is_available and replica.replication_lag <= max_lag)
        ]

        if not suitable_replicas:
            return None

        # 根据读策略选择从库
        import random

        if self.pool.read_strategy == "random":
            return random.choice(suitable_replicas).pool
        elif self.pool.read_strategy == "round_robin":
            self.pool._current_replica = (self.pool._current_replica + 1) % len(suitable_replicas)
            return suitable_replicas[self.pool._current_replica].pool
        elif self.pool.read_strategy == "weighted":
            total_weight = sum(r.weight for r in suitable_replicas)
            r = random.uniform(0, total_weight)
            for replica in suitable_replicas:
                r -= replica.weight
                if r <= 0:
                    return replica.pool

        return suitable_replicas[0].pool

    def clear_cache(self):
        """清空SQL解析缓存"""
        self._parse_cache.clear()

    def get_metrics(self) -> Dict:
        """获取路由器指标"""
        return {
            "cache_size": len(self._parse_cache),
            "force_master_keywords": list(self.force_master_keywords),
            "force_master_tables": list(self.force_master_tables),
            "allow_replica_lag": self.allow_replica_lag,
            "transaction_route_to_master": self.transaction_route_to_master,
        }
