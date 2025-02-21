"""
HTTP异常处理器模块
"""

from typing import Any, Dict, List

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from core.exceptions.handlers.base import ExceptionHandler
from core.exceptions.http.validation import ModelValidationException, RequestValidationException


class HTTPExceptionHandler(ExceptionHandler):
    """HTTP异常处理器"""

    async def handle_request_validation(self, request: Request, exc: RequestValidationError) -> None:
        """
        处理请求验证异常

        Args:
            request: FastAPI请求对象
            exc: 请求验证异常对象
        """
        errors = self._format_validation_errors(exc.errors())
        raise RequestValidationException(
            message="请求参数验证失败",
            errors=errors,
            context={"request_path": request.url.path},
        )

    async def handle_pydantic_validation(self, request: Request, exc: ValidationError) -> None:
        """
        处理Pydantic验证异常

        Args:
            request: FastAPI请求对象
            exc: Pydantic验证异常对象
        """
        errors = self._format_validation_errors(exc.errors())
        raise ModelValidationException(
            message="数据验证失败",
            errors=errors,
            context={"request_path": request.url.path},
        )

    def _format_validation_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化验证错误

        Args:
            errors: 原始错误列表

        Returns:
            格式化后的错误列表
        """
        formatted_errors = []
        for error in errors:
            error_info = {
                "loc": " -> ".join(str(x) for x in error["loc"]),
                "msg": error["msg"],
                "type": error["type"],
            }
            formatted_errors.append(error_info)
        return formatted_errors

    def unexpected_exception_handler(request: Request, exc: Exception) -> None:
        """
        处理未预期的异常

        Args:
            request: FastAPI请求对象
            exc: 未预期的异常对象

        Raises:
            Exception: 未处理的异常
        """
        pass
