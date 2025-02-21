"""
数据库监控中间件模块
"""

import logging
import time
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from core.config.setting import get_settings
from db.metrics.manager import monitor_manager

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()


class MonitorMiddleware(BaseHTTPMiddleware):
    """监控中间件"""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """处理请求"""
        # 记录开始时间
        start_time = time.time()

        try:
            # 调用下一个中间件
            response = await call_next(request)

            # 记录查询时间
            duration = time.time() - start_time
            monitor_manager.record_query(
                sql=f"{request.method} {request.url.path}",
                duration=duration,
            )

            # 记录缓存命中
            if "X-Cache" in response.headers:
                monitor_manager.record_cache(hit=response.headers["X-Cache"] == "HIT")

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Request failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise

        finally:
            # 记录连接
            monitor_manager.record_connection(
                active=len(request.scope.get("db_connections", [])),
                idle=0,  # TODO: 获取空闲连接数
            )


class QueryMonitorMiddleware:
    """查询监控中间件"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: Request) -> Any:
        """处理请求"""
        # 记录开始时间
        start_time = time.time()

        try:
            # 调用下一个中间件
            response = self.get_response(request)

            # 记录查询时间
            duration = time.time() - start_time
            monitor_manager.record_query(
                sql=f"{request.method} {request.url.path}",
                duration=duration,
            )

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Query failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class CacheMonitorMiddleware:
    """缓存监控中间件"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: Request) -> Any:
        """处理请求"""
        try:
            # 调用下一个中间件
            response = self.get_response(request)

            # 记录缓存命中
            if "X-Cache" in response.headers:
                monitor_manager.record_cache(hit=response.headers["X-Cache"] == "HIT")

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Cache failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class TransactionMonitorMiddleware:
    """事务监控中间件"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: Request) -> Any:
        """处理请求"""
        try:
            # 调用下一个中间件
            response = self.get_response(request)

            # 记录事务成功
            monitor_manager.record_transaction(success=True)

            return response

        except Exception as e:
            # 记录事务失败
            logger.error(f"Transaction failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise


class ConnectionMonitorMiddleware:
    """连接监控中间件"""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: Request) -> Any:
        """处理请求"""
        try:
            # 调用下一个中间件
            response = self.get_response(request)

            # 记录连接
            monitor_manager.record_connection(
                active=len(request.scope.get("db_connections", [])),
                idle=0,  # TODO: 获取空闲连接数
            )

            return response

        except Exception as e:
            # 记录错误
            logger.error(f"Connection failed: {e}")
            monitor_manager.record_transaction(success=False)
            raise
