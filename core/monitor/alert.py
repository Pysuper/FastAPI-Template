"""
监控告警模块
"""
import logging
import time
from typing import Any, Dict, List, Optional

from core.monitor.exceptions import MonitorError

logger = logging.getLogger(__name__)


class BaseAlert:
    """告警基类"""

    def __init__(self) -> None:
        self.alerts: List[Dict[str, Any]] = []
        self.start_time = time.time()

    def reset(self) -> None:
        """重置告警"""
        self.alerts = []
        self.start_time = time.time()

    def get_alerts(self) -> List[Dict[str, Any]]:
        """获取告警"""
        return self.alerts

    def get_duration(self) -> float:
        """获取持续时间"""
        return time.time() - self.start_time


class ConnectionAlert(BaseAlert):
    """连接告警"""

    def __init__(self) -> None:
        super().__init__()
        self.max_connections = 100
        self.max_idle_connections = 50
        self.max_active_connections = 80
        self.max_connection_errors = 10

    def check_connection(
        self,
        active: int = 0,
        idle: int = 0,
        errors: int = 0,
    ) -> None:
        """检查连接"""
        # 检查连接数
        if active + idle > self.max_connections:
            self.alerts.append(
                {
                    "type": "connection",
                    "level": "error",
                    "message": "连接数超过最大值",
                    "details": {
                        "active": active,
                        "idle": idle,
                        "max": self.max_connections,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查空闲连接数
        if idle > self.max_idle_connections:
            self.alerts.append(
                {
                    "type": "connection",
                    "level": "warning",
                    "message": "空闲连接数超过最大值",
                    "details": {
                        "idle": idle,
                        "max": self.max_idle_connections,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查活动连接数
        if active > self.max_active_connections:
            self.alerts.append(
                {
                    "type": "connection",
                    "level": "warning",
                    "message": "活动连接数超过最大值",
                    "details": {
                        "active": active,
                        "max": self.max_active_connections,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查连接错误数
        if errors > self.max_connection_errors:
            self.alerts.append(
                {
                    "type": "connection",
                    "level": "error",
                    "message": "连接错误数超过最大值",
                    "details": {
                        "errors": errors,
                        "max": self.max_connection_errors,
                    },
                    "timestamp": time.time(),
                }
            )


class QueryAlert(BaseAlert):
    """查询告警"""

    def __init__(self) -> None:
        super().__init__()
        self.max_query_time = 1.0
        self.max_slow_queries = 100
        self.max_query_errors = 10

    def check_query(
        self,
        duration: float = 0.0,
        slow_queries: int = 0,
        errors: int = 0,
    ) -> None:
        """检查查询"""
        # 检查查询时间
        if duration > self.max_query_time:
            self.alerts.append(
                {
                    "type": "query",
                    "level": "warning",
                    "message": "查询时间超过最大值",
                    "details": {
                        "duration": duration,
                        "max": self.max_query_time,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查慢查询数
        if slow_queries > self.max_slow_queries:
            self.alerts.append(
                {
                    "type": "query",
                    "level": "warning",
                    "message": "慢查询数超过最大值",
                    "details": {
                        "slow_queries": slow_queries,
                        "max": self.max_slow_queries,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查查询错误数
        if errors > self.max_query_errors:
            self.alerts.append(
                {
                    "type": "query",
                    "level": "error",
                    "message": "查询错误数超过最大值",
                    "details": {
                        "errors": errors,
                        "max": self.max_query_errors,
                    },
                    "timestamp": time.time(),
                }
            )


class TransactionAlert(BaseAlert):
    """事务告警"""

    def __init__(self) -> None:
        super().__init__()
        self.max_transaction_time = 5.0
        self.max_rollback_rate = 0.1
        self.max_transaction_errors = 10

    def check_transaction(
        self,
        duration: float = 0.0,
        rollback_rate: float = 0.0,
        errors: int = 0,
    ) -> None:
        """检查事务"""
        # 检查事务时间
        if duration > self.max_transaction_time:
            self.alerts.append(
                {
                    "type": "transaction",
                    "level": "warning",
                    "message": "事务时间超过最大值",
                    "details": {
                        "duration": duration,
                        "max": self.max_transaction_time,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查回滚率
        if rollback_rate > self.max_rollback_rate:
            self.alerts.append(
                {
                    "type": "transaction",
                    "level": "warning",
                    "message": "事务回滚率超过最大值",
                    "details": {
                        "rollback_rate": rollback_rate,
                        "max": self.max_rollback_rate,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查事务错误数
        if errors > self.max_transaction_errors:
            self.alerts.append(
                {
                    "type": "transaction",
                    "level": "error",
                    "message": "事务错误数超过最大值",
                    "details": {
                        "errors": errors,
                        "max": self.max_transaction_errors,
                    },
                    "timestamp": time.time(),
                }
            )


class CacheAlert(BaseAlert):
    """缓存告警"""

    def __init__(self) -> None:
        super().__init__()
        self.min_hit_rate = 0.5
        self.max_miss_rate = 0.5
        self.max_cache_errors = 10

    def check_cache(
        self,
        hit_rate: float = 0.0,
        miss_rate: float = 0.0,
        errors: int = 0,
    ) -> None:
        """检查缓存"""
        # 检查命中率
        if hit_rate < self.min_hit_rate:
            self.alerts.append(
                {
                    "type": "cache",
                    "level": "warning",
                    "message": "缓存命中率低于最小值",
                    "details": {
                        "hit_rate": hit_rate,
                        "min": self.min_hit_rate,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查未命中率
        if miss_rate > self.max_miss_rate:
            self.alerts.append(
                {
                    "type": "cache",
                    "level": "warning",
                    "message": "缓存未命中率超过最大值",
                    "details": {
                        "miss_rate": miss_rate,
                        "max": self.max_miss_rate,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查缓存错误数
        if errors > self.max_cache_errors:
            self.alerts.append(
                {
                    "type": "cache",
                    "level": "error",
                    "message": "缓存错误数超过最大值",
                    "details": {
                        "errors": errors,
                        "max": self.max_cache_errors,
                    },
                    "timestamp": time.time(),
                }
            )


class RateLimitAlert(BaseAlert):
    """限流告警"""

    def __init__(self) -> None:
        super().__init__()
        self.max_rejection_rate = 0.1
        self.max_rate_limit_errors = 10

    def check_rate_limit(
        self,
        rejection_rate: float = 0.0,
        errors: int = 0,
    ) -> None:
        """检查限流"""
        # 检查拒绝率
        if rejection_rate > self.max_rejection_rate:
            self.alerts.append(
                {
                    "type": "rate_limit",
                    "level": "warning",
                    "message": "限流拒绝率超过最大值",
                    "details": {
                        "rejection_rate": rejection_rate,
                        "max": self.max_rejection_rate,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查限流错误数
        if errors > self.max_rate_limit_errors:
            self.alerts.append(
                {
                    "type": "rate_limit",
                    "level": "error",
                    "message": "限流错误数超过最大值",
                    "details": {
                        "errors": errors,
                        "max": self.max_rate_limit_errors,
                    },
                    "timestamp": time.time(),
                }
            )


class CircuitBreakerAlert(BaseAlert):
    """熔断告警"""

    def __init__(self) -> None:
        super().__init__()
        self.max_failure_rate = 0.1
        self.max_circuit_breaker_errors = 10

    def check_circuit_breaker(
        self,
        failure_rate: float = 0.0,
        errors: int = 0,
    ) -> None:
        """检查熔断"""
        # 检查失败率
        if failure_rate > self.max_failure_rate:
            self.alerts.append(
                {
                    "type": "circuit_breaker",
                    "level": "warning",
                    "message": "熔断失败率超过最大值",
                    "details": {
                        "failure_rate": failure_rate,
                        "max": self.max_failure_rate,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查熔断错误数
        if errors > self.max_circuit_breaker_errors:
            self.alerts.append(
                {
                    "type": "circuit_breaker",
                    "level": "error",
                    "message": "熔断错误数超过最大值",
                    "details": {
                        "errors": errors,
                        "max": self.max_circuit_breaker_errors,
                    },
                    "timestamp": time.time(),
                }
            )


class RetryAlert(BaseAlert):
    """重试告警"""

    def __init__(self) -> None:
        super().__init__()
        self.max_retry_rate = 0.1
        self.max_retry_errors = 10

    def check_retry(
        self,
        retry_rate: float = 0.0,
        errors: int = 0,
    ) -> None:
        """检查重试"""
        # 检查重试率
        if retry_rate > self.max_retry_rate:
            self.alerts.append(
                {
                    "type": "retry",
                    "level": "warning",
                    "message": "重试率超过最大值",
                    "details": {
                        "retry_rate": retry_rate,
                        "max": self.max_retry_rate,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查重试错误数
        if errors > self.max_retry_errors:
            self.alerts.append(
                {
                    "type": "retry",
                    "level": "error",
                    "message": "重试错误数超过最大值",
                    "details": {
                        "errors": errors,
                        "max": self.max_retry_errors,
                    },
                    "timestamp": time.time(),
                }
            )


class TimeoutAlert(BaseAlert):
    """超时告警"""

    def __init__(self) -> None:
        super().__init__()
        self.max_timeout_rate = 0.1
        self.max_timeout_errors = 10

    def check_timeout(
        self,
        timeout_rate: float = 0.0,
        errors: int = 0,
    ) -> None:
        """检查超时"""
        # 检查超时率
        if timeout_rate > self.max_timeout_rate:
            self.alerts.append(
                {
                    "type": "timeout",
                    "level": "warning",
                    "message": "超时率超过最大值",
                    "details": {
                        "timeout_rate": timeout_rate,
                        "max": self.max_timeout_rate,
                    },
                    "timestamp": time.time(),
                }
            )

        # 检查超时错误数
        if errors > self.max_timeout_errors:
            self.alerts.append(
                {
                    "type": "timeout",
                    "level": "error",
                    "message": "超时错误数超过最大值",
                    "details": {
                        "errors": errors,
                        "max": self.max_timeout_errors,
                    },
                    "timestamp": time.time(),
                }
            ) 