"""
监控指标模块
实现统一的指标收集和导出
"""

from typing import Dict, Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary, generate_latest, multiprocess

from core.config.manager import config_manager


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        """初始化"""
        # 创建注册表
        self.registry = CollectorRegistry()

        # HTTP请求指标
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total count of HTTP requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
            registry=self.registry,
        )

        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "Number of HTTP requests in progress",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # 数据库指标
        self.db_connections_total = Gauge(
            "db_connections_total", "Total number of database connections", ["database"], registry=self.registry
        )

        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["database", "operation"],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
            registry=self.registry,
        )

        # 缓存指标
        self.cache_hits_total = Counter(
            "cache_hits_total", "Total number of cache hits", ["cache"], registry=self.registry
        )

        self.cache_misses_total = Counter(
            "cache_misses_total", "Total number of cache misses", ["cache"], registry=self.registry
        )

        # 业务指标
        self.business_operations_total = Counter(
            "business_operations_total",
            "Total count of business operations",
            ["operation", "status"],
            registry=self.registry,
        )

        self.business_operation_duration_seconds = Histogram(
            "business_operation_duration_seconds",
            "Business operation duration in seconds",
            ["operation"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
            registry=self.registry,
        )

        # 系统指标
        self.system_memory_bytes = Gauge(
            "system_memory_bytes", "System memory usage in bytes", ["type"], registry=self.registry
        )

        self.system_cpu_usage = Gauge(
            "system_cpu_usage", "System CPU usage percentage", ["cpu"], registry=self.registry
        )

    def track_request(self, method: str, endpoint: str, status: int, duration: float) -> None:
        """
        记录HTTP请求
        :param method: 请求方法
        :param endpoint: 请求端点
        :param status: 状态码
        :param duration: 持续时间
        """
        labels = {"method": method, "endpoint": endpoint}

        self.http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()

        self.http_request_duration_seconds.labels(**labels).observe(duration)

    def track_database_query(self, database: str, operation: str, duration: float) -> None:
        """
        记录数据库查询
        :param database: 数据库名称
        :param operation: 操作类型
        :param duration: 持续时间
        """
        self.db_query_duration_seconds.labels(database=database, operation=operation).observe(duration)

    def track_cache(self, cache: str, hit: bool) -> None:
        """
        记录缓存命中
        :param cache: 缓存名称
        :param hit: 是否命中
        """
        if hit:
            self.cache_hits_total.labels(cache=cache).inc()
        else:
            self.cache_misses_total.labels(cache=cache).inc()

    def track_business_operation(self, operation: str, status: str, duration: Optional[float] = None) -> None:
        """
        记录业务操作
        :param operation: 操作类型
        :param status: 状态
        :param duration: 持续时间
        """
        self.business_operations_total.labels(operation=operation, status=status).inc()

        if duration is not None:
            self.business_operation_duration_seconds.labels(operation=operation).observe(duration)

    def track_system_metrics(self, memory_usage: Dict[str, float], cpu_usage: Dict[str, float]) -> None:
        """
        记录系统指标
        :param memory_usage: 内存使用情况
        :param cpu_usage: CPU使用情况
        """
        for mem_type, value in memory_usage.items():
            self.system_memory_bytes.labels(type=mem_type).set(value)

        for cpu_id, value in cpu_usage.items():
            self.system_cpu_usage.labels(cpu=cpu_id).set(value)

    def increment(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        增加计数器值
        :param name: 指标名称
        :param value: 增加值
        :param labels: 标签
        """
        metric = getattr(self, name, None)
        if metric and isinstance(metric, Counter):
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        设置仪表值
        :param name: 指标名称
        :param value: 设置值
        :param labels: 标签
        """
        metric = getattr(self, name, None)
        if metric and isinstance(metric, Gauge):
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        观察直方图或摘要值
        :param name: 指标名称
        :param value: 观察值
        :param labels: 标签
        """
        metric = getattr(self, name, None)
        if metric and isinstance(metric, (Histogram, Summary)):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

    def get_metrics(self) -> bytes:
        """
        获取指标数据
        :return: 指标数据
        """
        if config_manager.metrics.MULTIPROCESS:
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            return generate_latest(registry)
        return generate_latest(self.registry)


# 创建默认指标收集器实例
metrics_collector = MetricsCollector()

# 导出
__all__ = ["metrics_collector", "MetricsCollector"]
