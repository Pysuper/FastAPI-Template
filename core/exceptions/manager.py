# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2025/1/2 17:23 
@Desc    ：异常管理器
"""
import logging
from typing import Dict, List, Type

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from core.exceptions.base.base_exception import BaseException
from core.exceptions.handlers.base import ExceptionHandler
from core.exceptions.handlers.http import HTTPExceptionHandler
from core.exceptions.handlers.system import SystemExceptionHandler
from core.exceptions.http.validation import ValidationException
from core.exceptions.middleware import ExceptionMiddleware
from core.exceptions.system.api import BusinessException
from core.exceptions.system.cache import CacheException
from core.exceptions.system.database import DatabaseException
from core.loge.manager import logic


class ExceptionManager:
    """异常管理器"""

    def __init__(self, app: FastAPI):
        """
        初始化异常管理器

        Args:
            app: FastAPI应用实例
        """
        self.app = app
        self.logger = logic
        self.exceptions: List[Exception] = []
        self.http_handler = HTTPExceptionHandler()
        self.system_handler = SystemExceptionHandler()
        self.handlers: Dict[Type[Exception], ExceptionHandler] = {}
        self._init_handlers()

    def _init_handlers(self) -> None:
        """初始化异常处理器"""
        # 基础异常处理器
        self.handlers[Exception] = self.system_handler
        self.handlers[HTTPException] = self.http_handler
        print(" ✅ BaseExceptionHandler")

        # 验证异常处理器
        self.handlers[ValidationError] = self.http_handler
        self.handlers[ValidationException] = self.http_handler
        print(" ✅ ValidationExceptionHandler")

        # 数据库异常处理器
        self.handlers[SQLAlchemyError] = self.system_handler
        self.handlers[DatabaseException] = self.system_handler
        print(" ✅ DatabaseExceptionHandler")

        # 缓存异常处理器
        self.handlers[RedisError] = self.system_handler
        self.handlers[CacheException] = self.system_handler
        print(" ✅ CacheExceptionHandler")

        # 认证异常处理器
        # TODO: 待实现
        print(" 🔰 AuthExceptionHandler")

        # 业务异常处理器
        self.handlers[BusinessException] = self.system_handler
        self.handlers[BaseException] = self.system_handler
        print(" ✅ BusinessExceptionHandler")

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
            self.add_exception(exc)
            handler = self._get_handler(exc)
            return await handler.handle(request, exc)
        except Exception as e:
            self.logger.error(f"Error handling exception: {str(e)}", exc_info=True)
            return await self.system_handler.handle(request, exc)

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

    def add_exception(self, exception: Exception) -> None:
        """
        添加异常记录

        Args:
            exception: 异常对象
        """
        self.exceptions.append(exception)

    def get_exceptions(self) -> List[Exception]:
        """
        获取异常记录

        Returns:
            异常记录列表
        """
        return self.exceptions

    def clear_exceptions(self) -> None:
        """清空异常记录"""
        self.exceptions.clear()

    def setup(self) -> None:
        """配置异常处理"""
        # 添加异常中间件
        self.app.add_middleware(ExceptionMiddleware)

        # 注册异常处理器
        for exc_type in self.handlers:
            self.app.add_exception_handler(exc_type, self.handle_exception)


def setup_exceptions(app: FastAPI) -> None:
    """
    设置异常处理器

    Args:
        app: FastAPI应用实例
    """
    manager = ExceptionManager(app)
    manager.setup()
