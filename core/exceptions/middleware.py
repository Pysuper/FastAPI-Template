"""
异常中间件模块
"""
import logging
from typing import Dict, Type

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from core.exceptions.base.base_exception import BaseException
from core.exceptions.handlers.base import ExceptionHandler
from core.exceptions.handlers.http import HTTPExceptionHandler
from core.exceptions.handlers.system import SystemExceptionHandler

logger = logging.getLogger(__name__)


class ExceptionMiddleware(BaseHTTPMiddleware):
    """异常处理中间件"""

    def __init__(self, app: ASGIApp):
        """
        初始化异常中间件
        
        Args:
            app: ASGI应用实例
        """
        super().__init__(app)
        self.handlers: Dict[Type[Exception], ExceptionHandler] = {}
        self.http_handler = HTTPExceptionHandler()
        self.system_handler = SystemExceptionHandler()
        self._init_handlers()

    def _init_handlers(self) -> None:
        """初始化异常处理器"""
        # 基础异常处理器
        self.handlers[Exception] = self.system_handler
        self.handlers[BaseException] = self.http_handler

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> JSONResponse:
        """
        处理请求
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            JSON响应对象
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)

    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        处理异常
        
        Args:
            request: FastAPI请求对象
            exc: 异常对象
            
        Returns:
            JSON响应对象
        """
        try:
            handler = self._get_handler(exc)
            return await handler.handle(request, exc)
        except Exception as e:
            logger.exception("Error handling exception", exc_info=e)
            return await self.system_handler.handle_unknown(request, exc)

    def _get_handler(self, exc: Exception) -> ExceptionHandler:
        """
        获取异常处理器
        
        Args:
            exc: 异常对象
            
        Returns:
            异常处理器实例
        """
        for exc_type, handler in self.handlers.items():
            if isinstance(exc, exc_type):
                return handler
        return self.system_handler


def setup_exception_handlers(app: ASGIApp) -> None:
    """
    配置异常处理器
    
    Args:
        app: ASGI应用实例
    """
    app.add_middleware(ExceptionMiddleware)
