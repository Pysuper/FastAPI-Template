# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：rate_limit.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：限流中间件
"""
import time
from typing import Dict, Optional, List

from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from core.exceptions.system.api import RateLimitException
from middlewares.base import BaseCustomMiddleware
from core.loge.logger import CustomLogger
from core.strong.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseCustomMiddleware):
    """限流中间件"""

    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 100,  # 每个时间窗口允许的请求数
        window: int = 60,  # 时间窗口大小(秒)
        exclude_paths: Optional[list] = None,  # 排除的路径
        whitelist: List[str] = None,  # IP白名单
        max_failures: int = 5,  # 最大失败次数
        failure_window: int = 300,  # 失败计数窗口(秒)
        failure_ban_time: int = 1800,  # 失败禁止时间(秒)
    ):
        super().__init__(app)
        self.limiter = RateLimiter(
            window_size=window,
            max_requests=max_requests,
            whitelist=whitelist,
            max_failures=max_failures,
            failure_window=failure_window,
            failure_ban_time=failure_ban_time,
        )
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.logger = CustomLogger("rate_limit")

    def _get_client_key(self, request: Request) -> str:
        """获取客户端标识"""
        return f"{request.client.host}:{request.url.path}"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求"""
        # 跳过不需要限流的路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_key = self._get_client_key(request)
        client_ip = request.client.host

        try:
            # 检查是否允许请求
            await self.limiter.acquire(client_key, client_ip)
            
            # 处理请求
            response = await call_next(request)
            
            # 如果是登录相关的请求，根据响应状态码记录成功/失败
            if request.url.path.endswith("/login"):
                if response.status_code == 200:
                    await self.limiter.record_success(client_key)
                elif response.status_code in (401, 403):
                    await self.limiter.record_failure(client_key, client_ip)
            
            return response

        except RateLimitException as e:
            self.logger.warning_with_extra(
                "请求超过限制",
                extra_fields={
                    "client_key": client_key,
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "method": request.method,
                }
            )
            raise RateLimitException(
                message=str(e),
                details={
                    "client_key": client_key,
                    "wait_time": e.wait_time,
                    "max_requests": self.limiter.max_requests,
                    "window": self.limiter.window_size,
                }
            )
