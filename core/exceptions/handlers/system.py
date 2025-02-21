"""
系统异常处理器模块
"""

import traceback
from typing import Any, Dict

from fastapi import Request
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from core.exceptions.handlers.base import ExceptionHandler
from core.exceptions.system.api import BusinessException
from core.exceptions.system.cache import RedisException
from core.exceptions.system.database import DatabaseException


class SystemExceptionHandler(ExceptionHandler):
    """系统异常处理器"""

    async def handle_sqlalchemy(self, request: Request, exc: SQLAlchemyError) -> None:
        """
        处理SQLAlchemy异常

        Args:
            request: FastAPI请求对象
            exc: SQLAlchemy异常对象
        """
        error_info = self._get_exception_info(exc)
        raise DatabaseException(
            message="数据库操作失败",
            details=error_info,
            context={"request_path": request.url.path},
        )

    async def handle_redis(self, request: Request, exc: RedisError) -> None:
        """
        处理Redis异常

        Args:
            request: FastAPI请求对象
            exc: Redis异常对象
        """
        error_info = self._get_exception_info(exc)
        raise RedisException(
            message="Redis操作失败",
            details=error_info,
            context={"request_path": request.url.path},
        )

    async def handle_unknown(self, request: Request, exc: Exception) -> None:
        """
        处理未知异常

        Args:
            request: FastAPI请求对象
            exc: 异常对象

        Returns:
            错误响应字典
        """
        error_info = self._get_exception_info(exc)
        raise BusinessException(
            message="系统内部错误",
            details=error_info,
            context={"request_path": request.url.path},
        )

    async def handle_business(self, request: Request, exc: BusinessException) -> None:
        """
        处理业务异常

        Args:
            request: FastAPI请求对象
            exc: 业务异常对象

        Returns:
            错误响应字典
        """
        error_info = self._get_exception_info(exc)
        raise BusinessException(
            message=exc.message,
            details=error_info,
            context={"request_path": request.url.path},
        )

    async def handle_event(self, request: Request, exc: Exception) -> None:
        """
        处理事件异常

        Args:
            request: FastAPI请求对象
            exc: 事件异常对象

        Returns:
            错误响应字典
        """
        error_info = self._get_exception_info(exc)
        raise BusinessException(
            message="事件处理失败",
            details=error_info,
            context={"request_path": request.url.path},
        )

    def _get_exception_info(self, exc: Exception) -> Dict[str, Any]:
        """
        获取异常信息

        Args:
            exc: 异常对象

        Returns:
            异常信息字典
        """
        return {
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
