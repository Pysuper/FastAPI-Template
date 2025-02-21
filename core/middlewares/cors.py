from typing import List

from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from core.config.setting import settings
from core.middlewares.base import BaseCustomMiddleware


class CORSConfig:
    """CORS配置类"""

    def __init__(
        self,
        allow_origins: List[str] = ["*"],
        allow_methods: List[str] = ["*"],
        allow_headers: List[str] = ["*"],
        allow_credentials: bool = True,
        expose_headers: List[str] = ["*"],
        max_age: int = 600,
    ):
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.allow_credentials = allow_credentials
        self.expose_headers = expose_headers
        self.max_age = max_age


class CORSMiddleware(BaseCustomMiddleware):
    """
    CORS中间件
    处理跨域请求
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # 添加CORS响应头
        response.headers["Access-Control-Allow-Origin"] = settings.CORS_ORIGINS
        response.headers["Access-Control-Allow-Credentials"] = str(settings.CORS_CREDENTIALS).lower()
        response.headers["Access-Control-Allow-Methods"] = ", ".join(settings.CORS_METHODS)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(settings.CORS_HEADERS)

        return response


class CustomCORSMiddleware(BaseCustomMiddleware):
    """自定义CORS中间件"""

    def initialize(self) -> None:
        """初始化CORS配置"""
        cors_config = self.config.get("cors", {})
        self.cors_config = CORSConfig(**cors_config)

        # 创建内部CORS中间件
        self.cors_middleware = CORSMiddleware(
            app=self.app,
            allow_origins=self.cors_config.allow_origins,
            allow_methods=self.cors_config.allow_methods,
            allow_headers=self.cors_config.allow_headers,
            allow_credentials=self.cors_config.allow_credentials,
            expose_headers=self.cors_config.expose_headers,
            max_age=self.cors_config.max_age,
        )
        print(" ✅ CustomCORSMiddleware")

    def _get_request_context(self, request: Request) -> dict:
        """获取请求上下文信息"""
        return {
            "method": request.method,
            "path": request.url.path,
            "headers": dict(request.headers),
            "client_host": request.client.host if request.client else None,
            "request_id": getattr(request.state, "request_id", None)
        }

    def _get_response_context(self, response: Response) -> dict:
        """获取响应上下文信息"""
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }

    async def process_request(self, request: Request) -> None:
        """处理请求"""
        if not self._should_process(request):
            return

        # 记录CORS请求信息
        origin = request.headers.get("origin")
        if origin:
            self.logger.debug("Processing CORS request", extra={"origin": origin, **self._get_request_context(request)})

    async def process_response(self, request: Request, response: Response) -> Response:
        """处理响应"""
        if not self._should_process(request):
            return response

        # 使用内部CORS中间件处理响应
        response = await self.cors_middleware(request, response)

        # 记录CORS响应信息
        origin = request.headers.get("origin")
        if origin:
            self.logger.debug(
                "Processed CORS response", extra={"origin": origin, **self._get_response_context(response)}
            )

        return response

    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """处理CORS异常"""
        self.logger.error(
            "CORS middleware error",
            exc_info=True,
            extra={"origin": request.headers.get("origin"), **self._get_request_context(request)},
        )
        return await super().handle_exception(request, exc)
