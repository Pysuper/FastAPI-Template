"""统一的日志中间件实现"""

import logging
import time
import uuid
from typing import Any, Dict, Optional

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from core.middlewares.base import BaseCustomMiddleware


class LoggingConfig:
    """日志配置"""

    def __init__(self, **kwargs):
        self.include_request_body = kwargs.get("include_request_body", False)
        self.include_response_body = kwargs.get("include_response_body", False)
        self.log_level = kwargs.get("log_level", logging.INFO)
        self.exclude_paths = kwargs.get("exclude_paths", ["/health", "/metrics"])
        self.request_id_header = kwargs.get("request_id_header", "X-Request-ID")


class LoggingMiddleware(BaseCustomMiddleware):
    """统一的日志中间件实现"""

    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        """初始化日志中间件
        
        Args:
            app: ASGI应用
            config: 中间件配置
        """
        super().__init__(app, config)
        self.initialize()
        print(" ✅ LoggingMiddleware")

    def initialize(self) -> None:
        """初始化日志配置"""
        logging_config = self.config.logging or {}
        self.logging_config = LoggingConfig(**logging_config)
        self.logger = logging.getLogger("api.access")

    def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """获取请求信息"""
        info = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_id": request.headers.get(self.logging_config.request_id_header),
        }

        if self.logging_config.include_request_body and hasattr(request, "body"):
            info["body"] = request.body

        return info

    def _get_response_info(self, response: Response) -> Dict[str, Any]:
        """获取响应信息"""
        info = {"status_code": response.status_code, "headers": dict(response.headers)}

        if self.logging_config.include_response_body:
            info["body"] = response.body

        return info

    async def process_request(self, request: Request) -> None:
        """处理请求"""
        if not self._should_process(request):
            return

        # 记录请求开始时间
        request.state.start_time = time.time()

        # 生成请求ID（如果没有）
        if not request.headers.get(self.logging_config.request_id_header):
            request.headers[self.logging_config.request_id_header] = str(uuid.uuid4())

        # 获取请求信息
        request_info = self._get_request_info(request)

        # 记录请求日志
        self.logger.log(
            self.logging_config.log_level,
            "Request received",
            extra={"request": request_info, **self._get_request_info(request)},
        )

    async def process_response(self, request: Request, response: Response) -> Response:
        """处理响应"""
        if not self._should_process(request):
            return response

        # 计算请求处理时间
        process_time = time.time() - getattr(request.state, "start_time", time.time())

        # 获取响应信息
        response_info = self._get_response_info(response)

        # 记录响应日志
        self.logger.log(
            self.logging_config.log_level,
            "Request completed",
            extra={
                "response": response_info,
                "process_time": process_time,
                **self._get_request_info(request),
            },
        )

        # 添加响应头
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        request_id = request.headers.get(self.logging_config.request_id_header)
        if request_id:
            response.headers[self.logging_config.request_id_header] = request_id

        return response

    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """处理异常"""
        self.logger.error(
            "Request failed",
            exc_info=True,
            extra={
                "error": str(exc),
                "error_type": exc.__class__.__name__,
                **self._get_request_info(request),
            },
        )
        return await super().handle_exception(request, exc)

