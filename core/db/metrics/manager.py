"""
数据库监控管理器模块
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional

from core.config.setting import get_settings
from db.metrics.metrics import (
    ConnectionMetrics,
    QueryMetrics,
    TransactionMetrics,
    CacheMetrics,
)

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()


class MonitorManager:
    """监控管理器"""

    def __init__(self):
        self._initialized = False
        self._collection_task: Optional[asyncio.Task] = None
        self._metrics = {
            "connection": ConnectionMetrics(),
            "query": QueryMetrics(),
            "transaction": TransactionMetrics(),
            "cache": CacheMetrics(),
        }
        self._start_time = time.time()

    async def init(self) -> None:
        """初始化监控"""
        if self._initialized:
            return

        try:
            # 启动指标收集任务
            self._collection_task = asyncio.create_task(self._collect_metrics())
            self._initialized = True
            logger.info("Monitor manager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize monitor manager: {e}")
            raise

    async def close(self) -> None:
        """关闭监控"""
        if not self._initialized:
            return

        try:
            # 取消指标收集任务
            if self._collection_task:
                self._collection_task.cancel()
                try:
                    await self._collection_task
                except asyncio.CancelledError:
                    pass
                self._collection_task = None

            self._initialized = False
            logger.info("Monitor manager closed")

        except Exception as e:
            logger.error(f"Failed to close monitor manager: {e}")
            raise

    async def _collect_metrics(self) -> None:
        """收集指标"""
        while True:
            try:
                # 收集各项指标
                for metrics in self._metrics.values():
                    metrics.collect()

                # 检查告警条件
                await self._check_alerts()

            except Exception as e:
                logger.error(f"Failed to collect metrics: {e}")

            await asyncio.sleep(settings.CACHE_MONITOR_INTERVAL)

    async def _check_alerts(self) -> None:
        """检查告警"""
        try:
            # 检查连接池告警
            connection_metrics = self._metrics["connection"]
            if connection_metrics.active_connections > connection_metrics.max_connections * 0.8:
                logger.warning("Connection pool usage is high")

            # 检查查询性能告警
            query_metrics = self._metrics["query"]
            if query_metrics.avg_query_time > 1.0:  # 1秒
                logger.warning("Query performance is slow")

            # 检查事务告警
            transaction_metrics = self._metrics["transaction"]
            if transaction_metrics.rollback_rate > 0.1:  # 10%
                logger.warning("Transaction rollback rate is high")

            # 检查缓存告警
            cache_metrics = self._metrics["cache"]
            if cache_metrics.miss_rate > 0.5:  # 50%
                logger.warning("Cache miss rate is high")

        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")

    def record_query(self, sql: str, duration: float) -> None:
        """记录查询"""
        self._metrics["query"].record_query(sql, duration)

    def record_connection(self, active: int, idle: int) -> None:
        """记录连接"""
        self._metrics["connection"].record_connection(active, idle)

    def record_transaction(self, success: bool) -> None:
        """记录事务"""
        self._metrics["transaction"].record_transaction(success)

    def record_cache(self, hit: bool) -> None:
        """记录缓存"""
        self._metrics["cache"].record_cache(hit)

    def get_metrics(self) -> Dict[str, dict]:
        """获取指标"""
        return {
            "uptime": int(time.time() - self._start_time),
            "connection": self._metrics["connection"].to_dict(),
            "query": self._metrics["query"].to_dict(),
            "transaction": self._metrics["transaction"].to_dict(),
            "cache": self._metrics["cache"].to_dict(),
        }

    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """获取慢查询"""
        return self._metrics["query"].get_slow_queries(limit)

    def get_query_stats(self) -> Dict:
        """获取查询统计"""
        return self._metrics["query"].get_stats()

    def get_connection_stats(self) -> Dict:
        """获取连接统计"""
        return self._metrics["connection"].get_stats()

    def get_transaction_stats(self) -> Dict:
        """获取事务统计"""
        return self._metrics["transaction"].get_stats()

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self._metrics["cache"].get_stats()


# 全局监控管理器实例
monitor_manager = MonitorManager()

# 导出
__all__ = ["monitor_manager", "MonitorManager"]
