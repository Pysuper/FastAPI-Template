import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """指标聚合器"""

    def __init__(
        self,
        collection_interval: int = 60,  # 收集间隔(秒)
        retention_days: int = 7,  # 保留天数
        enable_percentiles: bool = True,  # 是否计算百分位数
    ):
        self.collection_interval = collection_interval
        self.retention_days = retention_days
        self.enable_percentiles = enable_percentiles

        # 原始指标数据
        self._raw_metrics: Dict[str, List[Dict]] = defaultdict(list)  # metric_name -> [(timestamp, value)]

        # 聚合后的指标数据
        self._aggregated_metrics: Dict[str, Dict] = {}  # metric_name -> aggregated_data

        # 最后一次聚合时间
        self._last_aggregation: Dict[str, datetime] = {}

        # 聚合任务
        self._aggregation_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    def _clean_old_metrics(self):
        """清理过期指标"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)

        for metric_name in self._raw_metrics:
            self._raw_metrics[metric_name] = [
                (ts, value) for ts, value in self._raw_metrics[metric_name] if ts > cutoff
            ]

    def _calculate_percentiles(self, values: List[float], percentiles: List[float]) -> Dict[float, float]:
        """计算百分位数"""
        if not values:
            return {p: 0.0 for p in percentiles}

        sorted_values = sorted(values)
        result = {}

        for p in percentiles:
            k = (len(sorted_values) - 1) * p
            f = int(k)
            c = int(k) + 1 if k < len(sorted_values) - 1 else int(k)
            d = k - f
            result[p] = sorted_values[f] * (1 - d) + sorted_values[c] * d

        return result

    def _aggregate_metrics(self, metric_name: str):
        """聚合指标"""
        raw_data = self._raw_metrics[metric_name]
        if not raw_data:
            return

        # 获取时间范围
        now = datetime.now()
        start_time = now - timedelta(days=self.retention_days)

        # 按小时分组
        hourly_data = defaultdict(list)
        for ts, value in raw_data:
            if isinstance(value, (int, float)):
                hour = ts.replace(minute=0, second=0, microsecond=0)
                hourly_data[hour].append(value)

        # 计算聚合值
        aggregated = {
            "last_aggregation": now,
            "retention_days": self.retention_days,
            "hourly": {},
            "daily": {},
            "total": {
                "count": len(raw_data),
                "sum": sum(value for _, value in raw_data),
                "min": min(value for _, value in raw_data) if raw_data else 0,
                "max": max(value for _, value in raw_data) if raw_data else 0,
                "avg": sum(value for _, value in raw_data) / len(raw_data) if raw_data else 0,
            },
        }

        # 计算每小时统计
        for hour, values in hourly_data.items():
            stats = {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

            if self.enable_percentiles:
                percentiles = self._calculate_percentiles(values, [0.5, 0.75, 0.9, 0.95, 0.99])
                stats["percentiles"] = {f"p{int(p*100)}": value for p, value in percentiles.items()}

            aggregated["hourly"][hour.isoformat()] = stats

        # 计算每天统计
        daily_data = defaultdict(list)
        for hour, values in hourly_data.items():
            day = hour.date()
            daily_data[day].extend(values)

        for day, values in daily_data.items():
            stats = {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

            if self.enable_percentiles:
                percentiles = self._calculate_percentiles(values, [0.5, 0.75, 0.9, 0.95, 0.99])
                stats["percentiles"] = {f"p{int(p*100)}": value for p, value in percentiles.items()}

            aggregated["daily"][day.isoformat()] = stats

        self._aggregated_metrics[metric_name] = aggregated
        self._last_aggregation[metric_name] = now

    async def _aggregation_worker(self):
        """聚合工作器"""
        while not self._stop_event.is_set():
            try:
                # 清理过期数据
                self._clean_old_metrics()

                # 聚合每个指标
                for metric_name in list(self._raw_metrics.keys()):
                    last_aggregation = self._last_aggregation.get(metric_name)
                    if (
                        not last_aggregation
                        or (datetime.now() - last_aggregation).total_seconds() >= self.collection_interval
                    ):
                        self._aggregate_metrics(metric_name)

                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics aggregation: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """启动聚合器"""
        if self._aggregation_task is None:
            self._stop_event.clear()
            self._aggregation_task = asyncio.create_task(self._aggregation_worker())
            logger.info("Metrics aggregator started")

    async def stop(self):
        """停止聚合器"""
        if self._aggregation_task:
            self._stop_event.set()
            await self._aggregation_task
            self._aggregation_task = None
            logger.info("Metrics aggregator stopped")

    def add_metric(self, name: str, value: float):
        """添加指标"""
        self._raw_metrics[name].append((datetime.now(), value))

    def get_metrics(self, name: str = None) -> Dict:
        """获取指标"""
        if name:
            return self._aggregated_metrics.get(name, {})

        return {name: metrics for name, metrics in self._aggregated_metrics.items()}

    def get_current_metrics(self) -> Dict:
        """获取当前指标"""
        current = {}
        now = datetime.now()

        for name, raw_data in self._raw_metrics.items():
            # 只取最近一分钟的数据
            recent_values = [value for ts, value in raw_data if (now - ts).total_seconds() <= 60]

            if recent_values:
                current[name] = {
                    "count": len(recent_values),
                    "sum": sum(recent_values),
                    "min": min(recent_values),
                    "max": max(recent_values),
                    "avg": sum(recent_values) / len(recent_values),
                }

                if self.enable_percentiles:
                    percentiles = self._calculate_percentiles(recent_values, [0.5, 0.75, 0.9, 0.95, 0.99])
                    current[name]["percentiles"] = {f"p{int(p*100)}": value for p, value in percentiles.items()}

        return current
