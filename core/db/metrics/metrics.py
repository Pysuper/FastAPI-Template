"""
数据库监控指标模块
"""
import time
from collections import deque
from typing import Dict, List


class BaseMetrics:
    """基础指标类"""

    def __init__(self):
        self._start_time = time.time()

    def collect(self) -> None:
        """收集指标"""
        pass

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "uptime": int(time.time() - self._start_time),
        }

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.to_dict()


class ConnectionMetrics(BaseMetrics):
    """连接指标"""

    def __init__(self):
        super().__init__()
        self.active_connections = 0
        self.idle_connections = 0
        self.max_connections = 0
        self.total_connections = 0
        self.connection_timeouts = 0
        self.connection_errors = 0

    def record_connection(self, active: int, idle: int) -> None:
        """记录连接"""
        self.active_connections = active
        self.idle_connections = idle
        self.total_connections = active + idle

    def record_error(self, is_timeout: bool = False) -> None:
        """记录错误"""
        if is_timeout:
            self.connection_timeouts += 1
        else:
            self.connection_errors += 1

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            **super().to_dict(),
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "max_connections": self.max_connections,
            "total_connections": self.total_connections,
            "connection_timeouts": self.connection_timeouts,
            "connection_errors": self.connection_errors,
            "utilization": self.active_connections / max(1, self.max_connections),
        }


class QueryMetrics(BaseMetrics):
    """查询指标"""

    def __init__(self, max_slow_queries: int = 100):
        super().__init__()
        self.total_queries = 0
        self.total_time = 0.0
        self.min_time = float("inf")
        self.max_time = 0.0
        self.avg_time = 0.0
        self.slow_queries = deque(maxlen=max_slow_queries)
        self._current_minute = 0
        self._minute_queries = 0

    def record_query(self, sql: str, duration: float) -> None:
        """记录查询"""
        self.total_queries += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.total_queries

        # 记录慢查询
        if duration > 1.0:  # 1秒
            self.slow_queries.append({
                "sql": sql,
                "duration": duration,
                "timestamp": time.time(),
            })

        # 记录每分钟查询数
        current_minute = int(time.time() / 60)
        if current_minute != self._current_minute:
            self._current_minute = current_minute
            self._minute_queries = 0
        self._minute_queries += 1

    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """获取慢查询"""
        return sorted(
            self.slow_queries,
            key=lambda x: x["duration"],
            reverse=True,
        )[:limit]

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            **super().to_dict(),
            "total_queries": self.total_queries,
            "total_time": self.total_time,
            "min_time": self.min_time if self.min_time != float("inf") else 0,
            "max_time": self.max_time,
            "avg_time": self.avg_time,
            "qps": self._minute_queries / 60,
            "slow_queries": len(self.slow_queries),
        }


class TransactionMetrics(BaseMetrics):
    """事务指标"""

    def __init__(self):
        super().__init__()
        self.total_transactions = 0
        self.successful_transactions = 0
        self.failed_transactions = 0
        self.rollback_rate = 0.0
        self._current_minute = 0
        self._minute_transactions = 0

    def record_transaction(self, success: bool) -> None:
        """记录事务"""
        self.total_transactions += 1
        if success:
            self.successful_transactions += 1
        else:
            self.failed_transactions += 1

        self.rollback_rate = self.failed_transactions / max(1, self.total_transactions)

        # 记录每分钟事务数
        current_minute = int(time.time() / 60)
        if current_minute != self._current_minute:
            self._current_minute = current_minute
            self._minute_transactions = 0
        self._minute_transactions += 1

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            **super().to_dict(),
            "total_transactions": self.total_transactions,
            "successful_transactions": self.successful_transactions,
            "failed_transactions": self.failed_transactions,
            "rollback_rate": self.rollback_rate,
            "tps": self._minute_transactions / 60,
        }


class CacheMetrics(BaseMetrics):
    """缓存指标"""

    def __init__(self):
        super().__init__()
        self.total_operations = 0
        self.hits = 0
        self.misses = 0
        self.hit_rate = 0.0
        self.miss_rate = 0.0
        self._current_minute = 0
        self._minute_operations = 0

    def record_cache(self, hit: bool) -> None:
        """记录缓存"""
        self.total_operations += 1
        if hit:
            self.hits += 1
        else:
            self.misses += 1

        self.hit_rate = self.hits / max(1, self.total_operations)
        self.miss_rate = self.misses / max(1, self.total_operations)

        # 记录每分钟操作数
        current_minute = int(time.time() / 60)
        if current_minute != self._current_minute:
            self._current_minute = current_minute
            self._minute_operations = 0
        self._minute_operations += 1

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            **super().to_dict(),
            "total_operations": self.total_operations,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "ops": self._minute_operations / 60,
        } 