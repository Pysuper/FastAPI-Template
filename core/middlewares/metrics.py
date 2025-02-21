# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：metrics.py
@Author  ：PySuper
@Date    ：2024/12/24 17:12 
@Desc    ：Speedy metrics.py
"""
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from core.middlewares.prometheus import REQUESTS_IN_PROGRESS
from core.strong.monitoring import ACTIVE_REQUESTS, REQUEST_COUNT, REQUEST_LATENCY
from middlewares.base import BaseCustomMiddleware


class MetricsMiddleware(BaseCustomMiddleware):
    """
    性能监控中间件
    收集请求指标
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        endpoint = request.url.path

        # 记录正在处理的请求数
        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        # 记录请求开始时间
        start_time = time.time()

        try:
            response = await call_next(request)

            # 记录请求延迟
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)

            # 记录请求计数
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()

            return response
        except Exception as exc:
            # 记录异常请求
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
            raise
        finally:
            # 减少正在处理的请求数
            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


class MetricsMiddleware(BaseCustomMiddleware):
    """
    指标监控中间件
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录请求计数
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()

        # 记录请求延迟
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(process_time)
        
        print(" ✅ MetricsMiddleware")
        return response


class MonitorMiddleware(BaseCustomMiddleware):
    """
    监控中间件
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 记录请求开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录请求延迟
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(process_time)

        # 记录请求计数
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
        
        print(" ✅ MonitorMiddleware")
        return response
    
    async def after_response(
        self,
        request: Request,
        response: Response,
    ) -> Response:
        # 记录请求结束时间
        end_time = time.time()
        
        # 记录活��请求数
        ACTIVE_REQUESTS.labels(method=request.method, endpoint=request.url.path).dec()

        return response

        