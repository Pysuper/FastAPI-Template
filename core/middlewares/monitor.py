"""统一的监控中间件实现"""

import os
import random
import time
from typing import Any, Dict, Optional

import psutil
from fastapi import Request, Response
from pydantic import BaseModel, ConfigDict

from core.loge.manager import logic
from core.middlewares.base import BaseCustomMiddleware, MiddlewareConfig


class MonitorConfig(MiddlewareConfig):
    """监控配置"""

    enable_performance_monitoring: bool = True
    enable_memory_monitoring: bool = True
    enable_cpu_monitoring: bool = True
    sample_rate: float = 1.0  # 采样率
    slow_request_threshold: float = 1.0  # 慢请求阈值(秒)

    model_config = ConfigDict(extra="allow")


class RequestMetrics:
    """请求指标"""

    def __init__(self):
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.response_size: Optional[int] = None
        self.status_code: Optional[int] = None

    def finish(self, response: Response):
        """完成请求指标收集"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status_code = response.status_code
        self.response_size = len(response.body) if hasattr(response, "body") else 0


class SystemMetrics:
    """系统指标"""

    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            "rss": memory_info.rss / 1024 / 1024,  # MB
            "vms": memory_info.vms / 1024 / 1024,  # MB
        }

    @staticmethod
    def get_cpu_usage() -> float:
        """获取CPU使用率"""
        process = psutil.Process(os.getpid())
        return process.cpu_percent()


class PerformanceMonitorMiddleware(BaseCustomMiddleware):
    """性能监控中间件"""

    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = MonitorConfig(**(config or {}))
        # self.logger = get_logger("performance_monitor")
        self.logger = logic
        print(" ✅ PerformanceMonitorMiddleware")

    def _should_sample(self) -> bool:
        """是否需要采样"""
        return self.config.sample_rate >= 1.0 or random.random() < self.config.sample_rate

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        metrics = {}

        if self.config.enable_memory_monitoring:
            metrics["memory"] = SystemMetrics.get_memory_usage()

        if self.config.enable_cpu_monitoring:
            metrics["cpu"] = SystemMetrics.get_cpu_usage()

        return metrics

    def _log_metrics(self, request: Request, metrics: RequestMetrics, system_metrics: Dict[str, Any]):
        """记录性能指标"""
        if metrics.duration > self.config.slow_request_threshold:
            log_level = "WARNING"
        else:
            log_level = "INFO"

        self.logger.log(
            log_level,
            "Request performance metrics",
            extra={
                "request_id": self.get_request_id(request),
                "method": request.method,
                "path": request.url.path,
                "duration": metrics.duration,
                "status_code": metrics.status_code,
                "response_size": metrics.response_size,
                "system_metrics": system_metrics
            }
        )

    async def process_request(self, request: Request) -> None:
        """处理请求"""
        if not self._should_sample():
            return

        # 创建请求指标
        request.state.metrics = RequestMetrics()

    async def process_response(self, request: Request, response: Response) -> Response:
        """处理响应"""
        if not hasattr(request.state, "metrics"):
            return response

        # 完成请求指标收集
        metrics: RequestMetrics = request.state.metrics
        metrics.finish(response)

        # 收集系统指标
        system_metrics = self._collect_system_metrics()

        # 记录性能指标
        self._log_metrics(request, metrics, system_metrics)

        return response
