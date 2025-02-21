"""
缓存监控模块
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Set

from core.cache.base.interface import CacheBackend

logger = logging.getLogger(__name__)


class CacheMetric:
    """缓存指标"""

    def __init__(self, name: str, value: float, timestamp: Optional[float] = None):
        self.name = name
        self.value = value
        self.timestamp = timestamp or time.time()


class CacheAlert:
    """缓存告警"""

    def __init__(self, name: str, message: str, level: str = "warning", timestamp: Optional[float] = None):
        self.name = name
        self.message = message
        self.level = level
        self.timestamp = timestamp or time.time()


class AlertRule:
    """告警规则"""

    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, float]], bool],
        message: str,
        level: str = "warning",
        cooldown: int = 300,  # 告警冷却时间（秒）
    ):
        self.name = name
        self.condition = condition
        self.message = message
        self.level = level
        self.cooldown = cooldown
        self.last_alert_time: Optional[float] = None

    def should_alert(self, metrics: Dict[str, float]) -> bool:
        """检查是否应该告警"""
        if self.last_alert_time is None:
            return self.condition(metrics)

        if time.time() - self.last_alert_time >= self.cooldown:
            return self.condition(metrics)

        return False

    def mark_alerted(self):
        """标记已告警"""
        self.last_alert_time = time.time()


class CacheMonitor:
    """缓存监控器"""

    def __init__(
        self,
        cache: CacheBackend,
        collection_interval: int = 60,  # 指标收集间隔（秒）
        retention_days: int = 7,  # 指标保留天数
    ):
        self.cache = cache
        self.collection_interval = collection_interval
        self.retention_days = retention_days
        self._metrics: List[CacheMetric] = []
        self._alerts: List[CacheAlert] = []
        self._alert_rules: List[AlertRule] = []
        self._alert_handlers: Set[Callable[[CacheAlert], None]] = set()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self._alert_rules.append(rule)

    def add_alert_handler(self, handler: Callable[[CacheAlert], None]):
        """添加告警处理器"""
        self._alert_handlers.add(handler)

    def remove_alert_handler(self, handler: Callable[[CacheAlert], None]):
        """移除告警处理器"""
        self._alert_handlers.discard(handler)

    async def start(self):
        """启动监控"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """停止监控"""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitor_loop(self):
        """监控循环"""
        while self._monitoring:
            try:
                # 收集指标
                stats = await self.cache.get_stats()
                current_metrics = self._collect_metrics(stats)

                # 存储指标
                self._store_metrics(current_metrics)

                # 检查告警
                await self._check_alerts(current_metrics)

                # 清理过期指标
                self._cleanup_metrics()

                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)

    def _collect_metrics(self, stats: Dict[str, Any]) -> List[CacheMetric]:
        """收集指标"""
        metrics = []
        timestamp = time.time()

        # 处理通用指标
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                metrics.append(CacheMetric(key, float(value), timestamp))

        # 计算命中率
        if "hits" in stats and "misses" in stats:
            total = stats["hits"] + stats["misses"]
            if total > 0:
                hit_ratio = stats["hits"] / total
                metrics.append(CacheMetric("hit_ratio", hit_ratio, timestamp))

        return metrics

    def _store_metrics(self, metrics: List[CacheMetric]):
        """存储指标"""
        self._metrics.extend(metrics)

    async def _check_alerts(self, current_metrics: List[CacheMetric]):
        """检查告警"""
        # 转换为字典格式，方便规则检查
        metrics_dict = {m.name: m.value for m in current_metrics}

        for rule in self._alert_rules:
            if rule.should_alert(metrics_dict):
                alert = CacheAlert(rule.name, rule.message, rule.level)
                self._alerts.append(alert)
                rule.mark_alerted()

                # 触发告警处理器
                for handler in self._alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error(f"Error in alert handler: {e}")

    def _cleanup_metrics(self):
        """清理过期指标"""
        if not self._metrics:
            return

        cutoff_time = time.time() - (self.retention_days * 24 * 3600)
        self._metrics = [m for m in self._metrics if m.timestamp >= cutoff_time]

    def get_metrics(
        self,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
    ) -> List[CacheMetric]:
        """获取指标"""
        metrics = self._metrics

        if from_time:
            from_ts = from_time.timestamp()
            metrics = [m for m in metrics if m.timestamp >= from_ts]

        if to_time:
            to_ts = to_time.timestamp()
            metrics = [m for m in metrics if m.timestamp <= to_ts]

        return metrics

    def get_alerts(
        self,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        level: Optional[str] = None,
    ) -> List[CacheAlert]:
        """获取告警"""
        alerts = self._alerts

        if from_time:
            from_ts = from_time.timestamp()
            alerts = [a for a in alerts if a.timestamp >= from_ts]

        if to_time:
            to_ts = to_time.timestamp()
            alerts = [a for a in alerts if a.timestamp <= to_ts]

        if level:
            alerts = [a for a in alerts if a.level == level]

        return alerts
