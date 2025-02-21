"""
监控管理器模块
"""

import logging
import time
from typing import Any, Dict, List, Optional

from core.monitor.exceptions import MonitorError
from core.monitor.metrics import (
    BaseMetrics,
    CacheMetrics,
    CircuitBreakerMetrics,
    ConnectionMetrics,
    QueryMetrics,
    RateLimitMetrics,
    RetryMetrics,
    TimeoutMetrics,
    TransactionMetrics,
)

logger = logging.getLogger(__name__)


class MonitorManager:
    """监控管理器"""

    def __init__(self) -> None:
        # 初始化指标
        self.connection_metrics = ConnectionMetrics()
        self.query_metrics = QueryMetrics()
        self.transaction_metrics = TransactionMetrics()
        self.cache_metrics = CacheMetrics()
        self.rate_limit_metrics = RateLimitMetrics()
        self.circuit_breaker_metrics = CircuitBreakerMetrics()
        self.retry_metrics = RetryMetrics()
        self.timeout_metrics = TimeoutMetrics()

        # 初始化状态
        self.is_running = False
        self.start_time = 0.0

    async def init(self) -> None:
        """初始化监控管理器"""
        logger.info("Initializing monitor manager...")
        try:
            self.start()
            print(" ✅ MonitorManager")
            logger.info("Monitor manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize monitor manager: {str(e)}")
            raise

    async def close(self) -> None:
        """关闭监控管理器"""
        logger.info("Shutting down monitor manager...")
        try:
            self.stop()
            self.reset()
            logger.info("Monitor manager shut down successfully")
        except Exception as e:
            logger.error(f"Error during monitor manager shutdown: {str(e)}")
            raise

    def start(self) -> None:
        """启动监控"""
        if self.is_running:
            return

        self.is_running = True
        self.start_time = time.time()
        logger.info("Monitor started")

    def stop(self) -> None:
        """停止监控"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("Monitor stopped")

    def reset(self) -> None:
        """重置监控"""
        self.connection_metrics.reset()
        self.query_metrics.reset()
        self.transaction_metrics.reset()
        self.cache_metrics.reset()
        self.rate_limit_metrics.reset()
        self.circuit_breaker_metrics.reset()
        self.retry_metrics.reset()
        self.timeout_metrics.reset()
        logger.info("Monitor reset")

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return {
            "uptime": time.time() - self.start_time,
            "connection": self.connection_metrics.get_metrics(),
            "query": self.query_metrics.get_metrics(),
            "transaction": self.transaction_metrics.get_metrics(),
            "cache": self.cache_metrics.get_metrics(),
            "rate_limit": self.rate_limit_metrics.get_metrics(),
            "circuit_breaker": self.circuit_breaker_metrics.get_metrics(),
            "retry": self.retry_metrics.get_metrics(),
            "timeout": self.timeout_metrics.get_metrics(),
        }

    def record_connection(
        self,
        active: int = 0,
        idle: int = 0,
    ) -> None:
        """记录连接"""
        if not self.is_running:
            return

        try:
            self.connection_metrics.record_connection(active=active, idle=idle)
        except Exception as e:
            logger.error(f"Failed to record connection: {e}")

    def record_query(
        self,
        sql: str,
        duration: float,
    ) -> None:
        """记录查询"""
        if not self.is_running:
            return

        try:
            self.query_metrics.record_query(sql=sql, duration=duration)
        except Exception as e:
            logger.error(f"Failed to record query: {e}")

    def record_transaction(
        self,
        success: bool = True,
    ) -> None:
        """记录事务"""
        if not self.is_running:
            return

        try:
            self.transaction_metrics.record_transaction(success=success)
        except Exception as e:
            logger.error(f"Failed to record transaction: {e}")

    def record_cache(
        self,
        hit: bool = True,
    ) -> None:
        """记录缓存"""
        if not self.is_running:
            return

        try:
            self.cache_metrics.record_cache(hit=hit)
        except Exception as e:
            logger.error(f"Failed to record cache: {e}")

    def record_rate_limit(
        self,
        allowed: bool = True,
    ) -> None:
        """记录限流"""
        if not self.is_running:
            return

        try:
            self.rate_limit_metrics.record_request(allowed=allowed)
        except Exception as e:
            logger.error(f"Failed to record rate limit: {e}")

    def record_circuit_breaker(
        self,
        success: bool = True,
    ) -> None:
        """记录熔断"""
        if not self.is_running:
            return

        try:
            self.circuit_breaker_metrics.record_request(success=success)
        except Exception as e:
            logger.error(f"Failed to record circuit breaker: {e}")

    def record_retry(
        self,
        success: bool = True,
        retries: int = 0,
    ) -> None:
        """记录重试"""
        if not self.is_running:
            return

        try:
            self.retry_metrics.record_attempt(success=success, retries=retries)
        except Exception as e:
            logger.error(f"Failed to record retry: {e}")

    def record_timeout(
        self,
        success: bool = True,
        duration: float = 0.0,
    ) -> None:
        """记录超时"""
        if not self.is_running:
            return

        try:
            self.timeout_metrics.record_request(success=success, duration=duration)
        except Exception as e:
            logger.error(f"Failed to record timeout: {e}")

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
    ) -> None:
        """记录请求"""
        if not self.is_running:
            return

        try:
            # 记录查询
            self.record_query(sql=f"{method} {path}", duration=duration)

            # 记录事务
            self.record_transaction(success=status_code < 500)

            # 记录缓存
            self.record_cache(hit=status_code == 304)

            # 记录限流
            self.record_rate_limit(allowed=status_code != 429)

            # 记录熔断
            self.record_circuit_breaker(success=status_code < 500)

            # 记录超时
            self.record_timeout(success=status_code != 504, duration=duration)

        except Exception as e:
            logger.error(f"Failed to record request: {e}")


# 创建全局监控管理器实例
monitor_manager = MonitorManager()
