"""
异常处理器基类模块
"""

import logging
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from core.exceptions.base.base_exception import BaseException

logger = logging.getLogger(__name__)


class ExceptionHandler:
    """异常处理器基类"""

    def __init__(self):
        """初始化异常处理器"""
        self.logger = logging.getLogger(self.__class__.__name__)

    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        """
        处理异常

        Args:
            request: FastAPI请求对象
            exc: 异常对象

        Returns:
            JSON响应对象
        """
        error_info = self.get_error_info(exc)
        self.log_error(request, exc, error_info)
        return await self.create_response(request, exc)

    def get_error_info(self, exc: Exception) -> Dict[str, Any]:
        """
        获取错误信息

        Args:
            exc: 异常对象

        Returns:
            错误信息字典
        """
        if isinstance(exc, BaseException):
            return exc.to_dict()
        return {
            "code": "INTERNAL_ERROR",
            "message": str(exc),
            "details": self.get_error_details(exc),
        }

    def get_error_details(self, exc: Exception) -> Optional[Dict[str, Any]]:
        """
        获取错误详情

        Args:
            exc: 异常对象

        Returns:
            错误详情字典
        """
        return None

    def log_error(self, request: Request, exc: Exception, error_info: Dict[str, Any]) -> None:
        """
        记录错误日志

        Args:
            request: FastAPI请求对象
            exc: 异常对象
            error_info: 错误信息
        """
        context = self.get_error_context(request, exc)
        self.logger.error(
            f"Error handling request: {error_info['message']}",
            exc_info=exc,
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "url": str(request.url),
                "method": request.method,
                "error_info": error_info,
                **context,
            },
        )

    def get_error_context(self, request: Request, exc: Exception) -> Dict[str, Any]:
        """
        获取错误上下文

        Args:
            request: FastAPI请求对象
            exc: 异常对象

        Returns:
            错误上下文字典
        """
        context = {
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
            "user_id": getattr(request.state, "user_id", None),
        }

        if isinstance(exc, BaseException) and exc.context:
            context.update(exc.context)

        return context

    async def create_response(
        self,
        request: Request,
        exc: Exception,
        code: Optional[str] = None,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> JSONResponse:
        """
        创建错误响应

        Args:
            request: FastAPI请求对象
            exc: 异常对象
            code: 错误码
            message: 错误信息
            status_code: HTTP状态码
            details: 错误详情
            headers: 响应头

        Returns:
            JSON响应对象
        """
        if isinstance(exc, BaseException):
            return exc.to_response()

        error_info = self.get_error_info(exc)
        return JSONResponse(
            status_code=status_code or 500,
            content=error_info,
            headers=headers,
        )
