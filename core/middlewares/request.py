# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：request.py
@Author  ：PySuper
@Date    ：2024/12/24 17:15 
@Desc    ：Speedy request.py
"""
import time
from typing import Callable
import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from core.loge.manager import logic
from middlewares.base import BaseCustomMiddleware


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)


class RequestContextMiddleware(BaseCustomMiddleware):
    """
    请求上下文中间件
    处理请求ID、用户信息等
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 生成请求ID
        request.state.request_id = str(time.time_ns())

        # 记录请求开始时间
        request.state.start_time = time.time()

        # 调用下一个中间件
        response = await call_next(request)

        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request.state.request_id

        # 计算请求处理时间
        process_time = time.time() - request.state.start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        
        print(" ✅ RequestContextMiddleware")
        return response


class RequestLoggingMiddleware(BaseCustomMiddleware):
    """
    请求日志中间件
    """

    def __init__(self, app, config=None):
        super().__init__(app, config)
        self.logger = get_logger("request")
        print(" ✅ RequestLoggingMiddleware")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求开始
        start_time = time.time()

        # 生成请求ID
        request_id = request.headers.get("X-Request-ID", None)

        # 记录请求信息
        self.logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应信息
            self.logger.info(
                f"Request completed",
                extra={"request_id": request_id, "status_code": response.status_code, "process_time": process_time},
            )

            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)
            if request_id:
                response.headers["X-Request-ID"] = request_id
            
            return response

        except Exception as e:
            # 记录异常信息
            self.logger.error(f"Request failed", extra={"request_id": request_id, "error": str(e)})
            raise


class RequestIDMiddleware:
    pass


class TimingMiddleware:
    pass