import time
import uuid
import logging
from typing import Dict, Any, Optional

from fastapi import Request, Response
from pydantic import BaseModel, Field

from middlewares.base import BaseCustomMiddleware
from schemas.base.response import RequestResponseEndpoint
from core.loge.logger import CustomLogger


class TracingConfig(BaseModel):
    """追踪配置类"""

    header_name: str = Field(default="X-Request-ID", description="请求ID的头部名称")
    include_headers: list = Field(default_factory=list, description="需要包含的请求头")
    include_response_headers: list = Field(default_factory=list, description="需要包含的响应头")
    include_timing: bool = Field(default=True, description="是否包含时间信息")
    include_body: bool = Field(default=False, description="是否包含请求体")
    exclude_paths: list = Field(default_factory=lambda: ["/health", "/metrics"], description="排除的路径")


class TracingMiddleware(BaseCustomMiddleware):
    """追踪中间件"""

    def __init__(self, app, config=None):
        """初始化追踪中间件"""
        super().__init__(app, config)
        self.logger = CustomLogger("tracing")
        self.initialize()

    def initialize(self) -> None:
        """初始化追踪配置"""
        # 从配置中获取追踪配置，如果不存在则使用默认值
        tracing_dict = getattr(self.config, "tracing", {}) if self.config else {}
        self.tracing_config = TracingConfig(**tracing_dict)

    def _should_process(self, request: Request) -> bool:
        """检查是否需要处理请求"""
        return request.url.path not in self.tracing_config.exclude_paths

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求"""
        if not self._should_process(request):
            return await call_next(request)

        # 生成或获取请求ID
        request_id = request.headers.get(self.tracing_config.header_name, str(uuid.uuid4()))
        request.state.request_id = request_id

        # 记录请求开始时间
        if self.tracing_config.include_timing:
            request.state.start_time = time.time()

        # 记录追踪信息
        trace_info = self._get_trace_info(request)
        self.logger.info_with_extra(
            "Request trace started", extra_fields={"trace": trace_info, **self._get_request_context(request)}
        )

        try:
            # 处理请求
            response = await call_next(request)

            # 添加请求ID到响应头
            response.headers[self.tracing_config.header_name] = request.state.request_id

            # 获取追踪信息
            trace_info = self._get_trace_info(request, response)

            # 记录追踪信息
            self.logger.info_with_extra(
                "Request trace completed",
                extra_fields={
                    "trace": trace_info,
                    **self._get_request_context(request),
                    **self._get_response_context(response),
                },
            )

            return response
        except Exception as e:
            # 记录异常信息
            self.logger.error(
                "Request trace failed",
                extra={
                    "trace": trace_info,
                    "error": str(e),
                    "request_id": request.state.request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None,
                },
            )
            raise

    def _get_trace_info(self, request: Request, response: Optional[Response] = None) -> Dict[str, Any]:
        """获取追踪信息"""
        info = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # 添加指定的请求头
        if self.tracing_config.include_headers:
            headers = {}
            for header in self.tracing_config.include_headers:
                if header in request.headers:
                    headers[header] = request.headers[header]
            if headers:
                info["headers"] = headers

        # 添加响应信息
        if response:
            info["status_code"] = response.status_code

            # 添加指定的响应头
            if self.tracing_config.include_response_headers:
                headers = {}
                for header in self.tracing_config.include_response_headers:
                    if header in response.headers:
                        headers[header] = response.headers[header]
                if headers:
                    info["response_headers"] = headers

            # 添加处理时间
            if self.tracing_config.include_timing:
                start_time = getattr(request.state, "start_time", None)
                if start_time:
                    info["process_time"] = time.time() - start_time

        return info

    def _get_request_context(self, request: Request) -> Dict[str, Any]:
        """获取请求上下文"""
        return {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        }

    def _get_response_context(self, response: Response) -> Dict[str, Any]:
        """获取响应上下文"""
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }
