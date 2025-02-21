"""统一的拦截器中间件实现"""

from abc import ABC, abstractmethod
from typing import Any, List, Callable, Awaitable, Dict, Optional

from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from middlewares.base import BaseCustomMiddleware


class InterceptorConfig(BaseModel):
    """拦截器配置"""

    enabled: bool = True
    exclude_paths: list = ["/health", "/metrics"]

    class Config:
        extra = "allow"


class BaseInterceptor(ABC):
    """拦截器基类"""

    @abstractmethod
    async def before_request(self, request: Request) -> None:
        """请求前处理"""
        pass

    @abstractmethod
    async def after_request(self, request: Request, response: Response) -> None:
        """请求后处理"""
        pass

    async def on_error(self, request: Request, exc: Exception) -> None:
        """错误处理"""
        pass


class RequestInterceptor(BaseInterceptor):
    """请求拦截器基类"""

    pass


class ResponseInterceptor(BaseInterceptor):
    """响应拦截器基类"""

    async def before_response(self, response: Response) -> None:
        """响应前处理"""
        pass

    async def after_response(self, response: Response) -> None:
        """响应后处理"""
        pass


class InterceptorMiddleware(BaseCustomMiddleware):
    """拦截器中间件
    
    提供请求和响应拦截功能
    支持添加多个拦截器
    """
    
    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app, config)
        self.request_interceptors = []
        self.response_interceptors = []
        print(" ✅ InterceptorMiddleware")
        
    def add_request_interceptor(self, interceptor: Callable[[Request], Awaitable[None]]) -> None:
        """添加请求拦截器"""
        self.request_interceptors.append(interceptor)
        
    def add_response_interceptor(self, interceptor: Callable[[Request, Response], Awaitable[None]]) -> None:
        """添加响应拦截器"""
        self.response_interceptors.append(interceptor)

    async def _execute_interceptors(
        self,
        interceptors: List[BaseInterceptor],
        method_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """执行拦截器"""
        for interceptor in interceptors:
            try:
                method = getattr(interceptor, method_name)
                await method(*args, **kwargs)
            except Exception as e:
                self.logger.error(
                    f"Interceptor {interceptor.__class__.__name__} error",
                    exc_info=True,
                    extra={
                        "method": method_name,
                        "error": str(e),
                        "error_type": e.__class__.__name__,
                    },
                )
                await interceptor.on_error(args[0], e)

    async def process_request(self, request: Request) -> None:
        """处理请求"""
        if not self._should_process(request):
            return

        # 执行请求前拦截器
        await self._execute_interceptors(
            self.request_interceptors,
            "before_request",
            request,
        )

    async def process_response(self, request: Request, response: Response) -> Response:
        """处理响应"""
        if not self._should_process(request):
            return response

        try:
            # 执行响应前拦截器
            for interceptor in self.response_interceptors:
                try:
                    await interceptor.before_response(response)
                except Exception as e:
                    await interceptor.on_error(request, e)

            # 执行请求后拦截器
            await self._execute_interceptors(
                self.request_interceptors,
                "after_request",
                request,
                response,
            )

            # 执行响应后拦截器
            for interceptor in self.response_interceptors:
                try:
                    await interceptor.after_response(response)
                except Exception as e:
                    await interceptor.on_error(request, e)

            return response

        except Exception as e:
            self.logger.error(
                "Interceptor process response error",
                exc_info=True,
                extra={
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    **self._get_request_context(request),
                },
            )
            raise

    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """处理异常"""
        # 执行所有拦截器的错误处理
        for interceptor in self.request_interceptors + self.response_interceptors:
            try:
                await interceptor.on_error(request, exc)
            except Exception as e:
                self.logger.error(
                    f"Interceptor error handler failed: {str(e)}",
                    exc_info=True,
                )

        return await super().handle_exception(request, exc)
