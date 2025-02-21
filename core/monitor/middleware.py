"""
监控中间件模块
"""
import logging
import time
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from core.monitor.exceptions import MonitorError
from core.monitor.manager import monitor_manager

logger = logging.getLogger(__name__)


class MonitorMiddleware(BaseHTTPMiddleware):
    """监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # 记录开始时间
        start_time = time.time()

        try:
            # 执行请求
            response = await call_next(request)

            # 记录请求时间
            duration = time.time() - start_time
            monitor_manager.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
            )

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Request failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class QueryMonitorMiddleware(BaseHTTPMiddleware):
    """查询监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # 记录开始时间
        start_time = time.time()

        try:
            # 执行请求
            response = await call_next(request)

            # 记录查询时间
            duration = time.time() - start_time
            monitor_manager.record_query(
                sql=str(request.url.path),
                duration=duration,
            )

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Query failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class CacheMonitorMiddleware(BaseHTTPMiddleware):
    """缓存监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            # 执行请求
            response = await call_next(request)

            # 记录缓存命中
            monitor_manager.record_cache(hit=response.status_code == 304)

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Cache failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class TransactionMonitorMiddleware(BaseHTTPMiddleware):
    """事务监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            # 执行请求
            response = await call_next(request)

            # 记录事务成功
            monitor_manager.record_transaction(success=True)

            return response

        except Exception as e:
            # 记录事务失败
            logger.error(f"Transaction failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class ConnectionMonitorMiddleware(BaseHTTPMiddleware):
    """连接监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            # 执行请求
            response = await call_next(request)

            # 记录连接
            monitor_manager.record_connection(
                active=1,  # TODO: 获取活动连接数
                idle=0,  # TODO: 获取空闲连接数
            )

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Connection failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class RateLimitMonitorMiddleware(BaseHTTPMiddleware):
    """限流监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            # 执行请求
            response = await call_next(request)

            # 记录请求
            monitor_manager.record_rate_limit(allowed=response.status_code != 429)

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Rate limit failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class CircuitBreakerMonitorMiddleware(BaseHTTPMiddleware):
    """熔断监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            # 执行请求
            response = await call_next(request)

            # 记录请求
            monitor_manager.record_circuit_breaker(success=response.status_code < 500)

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Circuit breaker failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class RetryMonitorMiddleware(BaseHTTPMiddleware):
    """重试监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        retries = 0
        max_retries = 3

        while True:
            try:
                # 执行请求
                response = await call_next(request)

                # 记录请求
                monitor_manager.record_retry(success=True, retries=retries)

                return response

            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    # 记录错误
                    logger.error(f"Retry failed: {e}")
                    monitor_manager.record_retry(success=False, retries=retries)
                    raise

                logger.warning(f"Retry attempt {retries}: {e}")


class TimeoutMonitorMiddleware(BaseHTTPMiddleware):
    """超时监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # 记录开始时间
        start_time = time.time()

        try:
            # 执行请求
            response = await call_next(request)

            # 记录请求时间
            duration = time.time() - start_time
            monitor_manager.record_timeout(success=True, duration=duration)

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Timeout failed: {e}")
            monitor_manager.record_timeout(success=False, duration=time.time() - start_time)
            raise 