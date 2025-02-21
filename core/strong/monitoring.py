import os
from datetime import datetime
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest, multiprocess

from core.config.setting import settings

# Prometheus指标
REQUEST_COUNT = Counter(
    "http_request_count",
    "HTTP Request Count",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP Request Latency",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of active HTTP requests",
    ["method", "endpoint"],
)

DB_CONNECTION_POOL = Gauge(
    "db_connection_pool",
    "Database Connection Pool Stats",
    ["type", "status"],
)

REDIS_CONNECTION_POOL = Gauge(
    "redis_connection_pool",
    "Redis Connection Pool Stats",
    ["type", "status"],
)

CELERY_TASK_COUNT = Counter(
    "celery_task_count",
    "Celery Task Count",
    ["task_name", "status"],
)

CELERY_TASK_LATENCY = Histogram(
    "celery_task_latency_seconds",
    "Celery Task Latency",
    ["task_name"],
)


class MonitoringManager:
    """监控管理器"""

    def __init__(self):
        self._tracer_provider: Optional[TracerProvider] = None
        self._meter_provider: Optional[MeterProvider] = None
        self._registry: Optional[CollectorRegistry] = None
        self._start_time: Optional[datetime] = None

    def setup_monitoring(self, app=None):
        """设置监控"""
        self._start_time = datetime.now()

        # 设置OpenTelemetry
        self._setup_tracing()
        self._setup_metrics()

        # 设置Prometheus
        self._setup_prometheus()

        # 设置应用程序监控
        if app:
            self._setup_app_monitoring(app)

    def _setup_tracing(self):
        """设置分布式追踪"""
        # 创建TracerProvider
        self._tracer_provider = TracerProvider()

        # 添加OTLP导出器
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4317"),
            insecure=True,
        )
        self._tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # 设置全局TracerProvider
        trace.set_tracer_provider(self._tracer_provider)

    def _setup_metrics(self):
        """设置指标收集"""
        # 创建PrometheusMetricReader
        reader = PrometheusMetricReader()

        # 创建MeterProvider
        self._meter_provider = MeterProvider(metric_readers=[reader])

        # 设置全局MeterProvider
        metrics.set_meter_provider(self._meter_provider)

    def _setup_prometheus(self):
        """设置Prometheus"""
        # 设置多进程模式
        if "PROMETHEUS_MULTIPROC_DIR" not in os.environ:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = settings.PROMETHEUS_MULTIPROC_DIR

        # 创建注册表
        self._registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(self._registry)

    def _setup_app_monitoring(self, app):
        """设置应用程序监控"""
        # FastAPI监控
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=self._tracer_provider,
            meter_provider=self._meter_provider,
        )

        # SQLAlchemy监控
        SQLAlchemyInstrumentor().instrument(
            tracer_provider=self._tracer_provider,
            meter_provider=self._meter_provider,
        )

        # Redis监控
        RedisInstrumentor().instrument(
            tracer_provider=self._tracer_provider,
            meter_provider=self._meter_provider,
        )

        # Celery监控
        CeleryInstrumentor().instrument(
            tracer_provider=self._tracer_provider,
            meter_provider=self._meter_provider,
        )

    def track_request(self, method: str, endpoint: str, status: int, duration: float):
        """跟踪HTTP请求"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    def track_active_request(self, method: str, endpoint: str, is_start: bool = True):
        """跟踪活动请求"""
        if is_start:
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
        else:
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()

    def track_db_pool(self, pool_type: str, status: str, value: float):
        """跟踪数据库连接池"""
        DB_CONNECTION_POOL.labels(type=pool_type, status=status).set(value)

    def track_redis_pool(self, pool_type: str, status: str, value: float):
        """跟踪Redis连接池"""
        REDIS_CONNECTION_POOL.labels(type=pool_type, status=status).set(value)

    def track_celery_task(self, task_name: str, status: str, duration: float = None):
        """跟踪Celery任务"""
        CELERY_TASK_COUNT.labels(task_name=task_name, status=status).inc()
        if duration is not None:
            CELERY_TASK_LATENCY.labels(task_name=task_name).observe(duration)

    def get_metrics(self) -> bytes:
        """获取指标数据"""
        return generate_latest(self._registry)

    def get_health(self) -> dict:
        """获取健康状态"""
        return {
            "status": "healthy",
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime_seconds": ((datetime.now() - self._start_time).total_seconds() if self._start_time else None),
        }


# 创建全局���控管理器实例
monitoring_manager = MonitoringManager()
