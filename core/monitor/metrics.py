"""
监控指标模块
"""
import time
from typing import Any, Dict, List, Optional

from core.monitor.exceptions import MonitorError


class BaseMetrics:
    """指标基类"""

    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {}
        self.start_time = time.time()

    def reset(self) -> None:
        """重置指标"""
        self.metrics = {}
        self.start_time = time.time()

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return self.metrics

    def get_duration(self) -> float:
        """获取持续时间"""
        return time.time() - self.start_time


class ConnectionMetrics(BaseMetrics):
    """连接指标"""

    def __init__(self) -> None:
        super().__init__()
        self.metrics = {
            "active_connections": 0,
            "idle_connections": 0,
            "total_connections": 0,
            "connection_errors": 0,
        }

    def record_connection(
        self,
        active: int = 0,
        idle: int = 0,
    ) -> None:
        """记录连接"""
        self.metrics["active_connections"] = active
        self.metrics["idle_connections"] = idle
        self.metrics["total_connections"] = active + idle

    def record_error(self) -> None:
        """记录错误"""
        self.metrics["connection_errors"] += 1


class QueryMetrics(BaseMetrics):
    """查询指标"""

    def __init__(self) -> None:
        super().__init__()
        self.metrics = {
            "total_queries": 0,
            "total_duration": 0.0,
            "average_duration": 0.0,
            "query_errors": 0,
            "queries": [],
        }

    def record_query(
        self,
        sql: str,
        duration: float,
    ) -> None:
        """记录查询"""
        self.metrics["total_queries"] += 1
        self.metrics["total_duration"] += duration
        self.metrics["average_duration"] = (
            self.metrics["total_duration"] / self.metrics["total_queries"]
        )
        self.metrics["queries"].append(
            {
                "sql": sql,
                "duration": duration,
                "timestamp": time.time(),
            }
        )

    def record_error(self) -> None:
        """记录错误"""
        self.metrics["query_errors"] += 1


class TransactionMetrics(BaseMetrics):
    """事务指标"""

    def __init__(self) -> None:
        super().__init__()
        self.metrics = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "success_rate": 0.0,
        }

    def record_transaction(
        self,
        success: bool = True,
    ) -> None:
        """记录事务"""
        self.metrics["total_transactions"] += 1
        if success:
            self.metrics["successful_transactions"] += 1
        else:
            self.metrics["failed_transactions"] += 1
        self.metrics["success_rate"] = (
            self.metrics["successful_transactions"] / self.metrics["total_transactions"]
        )


class CacheMetrics(BaseMetrics):
    """缓存指标"""

    def __init__(self) -> None:
        super().__init__()
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0,
        }

    def record_cache(
        self,
        hit: bool = True,
    ) -> None:
        """记录缓存"""
        self.metrics["total_requests"] += 1
        if hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
        self.metrics["hit_rate"] = self.metrics["cache_hits"] / self.metrics["total_requests"]


class RateLimitMetrics(BaseMetrics):
    """限流指标"""

    def __init__(self) -> None:
        super().__init__()
        self.metrics = {
            "total_requests": 0,
            "allowed_requests": 0,
            "rejected_requests": 0,
            "rejection_rate": 0.0,
        }

    def record_request(
        self,
        allowed: bool = True,
    ) -> None:
        """记录请求"""
        self.metrics["total_requests"] += 1
        if allowed:
            self.metrics["allowed_requests"] += 1
        else:
            self.metrics["rejected_requests"] += 1
        self.metrics["rejection_rate"] = (
            self.metrics["rejected_requests"] / self.metrics["total_requests"]
        )


class CircuitBreakerMetrics(BaseMetrics):
    """熔断指标"""

    def __init__(self) -> None:
        super().__init__()
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_open_count": 0,
            "last_failure_time": 0,
            "current_state": "closed",
        }

    def record_request(
        self,
        success: bool = True,
    ) -> None:
        """记录请求"""
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
            self.metrics["last_failure_time"] = time.time()

    def record_circuit_open(self) -> None:
        """记录熔断开启"""
        self.metrics["circuit_open_count"] += 1
        self.metrics["current_state"] = "open"

    def record_circuit_close(self) -> None:
        """记录熔断关闭"""
        self.metrics["current_state"] = "closed"


class RetryMetrics(BaseMetrics):
    """重试指标"""

    def __init__(self) -> None:
        super().__init__()
        self.metrics = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "retry_count": 0,
            "average_retries": 0.0,
        }

    def record_attempt(
        self,
        success: bool = True,
        retries: int = 0,
    ) -> None:
        """记录尝试"""
        self.metrics["total_attempts"] += 1
        if success:
            self.metrics["successful_attempts"] += 1
        else:
            self.metrics["failed_attempts"] += 1
        self.metrics["retry_count"] += retries
        self.metrics["average_retries"] = (
            self.metrics["retry_count"] / self.metrics["total_attempts"]
        )


class TimeoutMetrics(BaseMetrics):
    """超时指标"""

    def __init__(self) -> None:
        super().__init__()
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "timeout_requests": 0,
            "timeout_rate": 0.0,
            "average_response_time": 0.0,
        }

    def record_request(
        self,
        success: bool = True,
        duration: float = 0.0,
    ) -> None:
        """记录请求"""
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["timeout_requests"] += 1
        self.metrics["timeout_rate"] = (
            self.metrics["timeout_requests"] / self.metrics["total_requests"]
        )
        self.metrics["average_response_time"] = (
            (self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1) + duration)
            / self.metrics["total_requests"]
        ) 