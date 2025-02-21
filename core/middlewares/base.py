"""
@Project ：Speedy 
@File    ：base.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：中间件基础模块

提供统一的中间件基类和常用中间件实现
支持请求处理、响应处理、异常处理等功能
"""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, TypeVar

from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

from core.loge.logger import CustomLogger
from core.loge.manager import logic

# 类型变量
T = TypeVar("T")


class MiddlewareConfig(BaseModel):
    """中间件配置基类

    提供中间件的基本配置选项
    支持启用/禁用、路径排除、日志级别等设置
    """

    enabled: bool = Field(default=True, description="是否启用中间件")
    exclude_paths: List[str] = Field(default=["/health", "/metrics"], description="排除的路径列表")
    log_level: str = Field(default="INFO", description="日志级别")
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
    cache_ttl: int = Field(default=300, description="缓存过期时间(秒)")
    rate_limit: Optional[Dict[str, Any]] = Field(default=None, description="速率限制配置")
    cors_settings: Optional[Dict[str, Any]] = Field(default=None, description="CORS配置")
    logging: Optional[Dict[str, Any]] = Field(default=None, description="日志配置")
    
    # 自定义配置项
    compression_min_size: int = Field(default=1024, description="压缩最小字节数")
    compression_level: int = Field(default=6, description="压缩级别(1-9)")
    compression_algorithms: List[str] = Field(default=["gzip", "deflate"], description="压缩算法列表")
    compression_types: List[str] = Field(default=["text/html", "text/css", "text/xml", "application/json"], description="压缩类型列表")
    

    class Config:
        extra = "allow"


class BaseCustomMiddleware(BaseHTTPMiddleware):
    """统一的中间件基类

    提供中间件的基本功能和通用实现
    支持请求前处理、响应后处理、异常处理等
    """

    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        """初始化中间件

        Args:
            app: ASGI应用
            config: 中间件配置
        """
        super().__init__(app)
        self.config = MiddlewareConfig(**(config or {}))
        # self.logger = CustomLogger(self.__class__.__name__)
        self.logger = logic

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求的主要方法

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象

        Raises:
            Exception: 处理过程中的异常
        """
        if not self._should_process(request):
            return await call_next(request)

        request.state.start_time = time.time()
        request.state.request_id = self._get_request_id(request)
        request.state.context = {}  # 用于存储请求上下文数据

        try:
            # 前置处理
            await self.before_request(request)

            # 处理请求
            response = await call_next(request)

            # 后置处理
            response = await self.after_response(request, response)

            # 添加通用响应头
            self._add_common_headers(request, response)

            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)
        finally:
            # TODO: 记录请求处理时间
            # self._log_request_time(request)
            # 清理请求上下文
            self._cleanup_context(request)

    def _should_process(self, request: Request) -> bool:
        """判断是否需要处理请求

        Args:
            request: 请求对象

        Returns:
            是否需要处理
        """
        if not self.config.enabled:
            return False

        # 检查是否在排除路径中
        path = request.url.path
        return not any(path.startswith(excluded) for excluded in self.config.exclude_paths)

    def _get_request_id(self, request: Request) -> str:
        """获取或生成请求ID

        Args:
            request: 请求对象

        Returns:
            请求ID
        """
        return request.headers.get("X-Request-ID", str(uuid.uuid4()))

    def _log_request_time(self, request: Request) -> None:
        """记录请求处理时间

        Args:
            request: 请求对象
        """
        process_time = time.time() - request.state.start_time
        self.logger.info(
            "请求处理完成",
            extra={
                "request_id": request.state.request_id,
                "path": request.url.path,
                "method": request.method,
                "process_time": process_time,
                "client_ip": request.client.host if request.client else None
            }
        )

    def _add_common_headers(self, request: Request, response: Response) -> None:
        """添加通用响应头

        Args:
            request: 请求对象
            response: 响应对象
        """
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time"] = f"{time.time() - request.state.start_time:.3f}s"

    def _cleanup_context(self, request: Request) -> None:
        """清理请求上下文

        Args:
            request: 请求对象
        """
        request.state.context.clear()

    async def before_request(self, request: Request) -> None:
        """请求前处理(子类可重写)

        Args:
            request: 请求对象
        """
        pass

    async def after_response(self, request: Request, response: Response) -> Response:
        """响应后处理(子类可重写)

        Args:
            request: 请求对象
            response: 响应对象

        Returns:
            处理后的响应对象
        """
        return response

    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """异常处理(子类可重写)

        Args:
            request: 请求对象
            exc: 异常对象

        Returns:
            错误响应对象

        Raises:
            Exception: 未处理的异常
        """
        self.logger.error(
            "请求处理异常",
            extra={
                "request_id": request.state.request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(exc),
                "error_type": exc.__class__.__name__,
                "client_ip": request.client.host if request.client else None
            },
            exc_info=True
        )
        raise exc


class BaseAuthMiddleware(BaseCustomMiddleware):
    """认证中间件基类

    提供用户认证的基本功能
    支持多种认证方式和认证结果缓存
    """

    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None) -> None:
        """初始化

        Args:
            app: ASGI应用
            config: 中间件配置
        """
        super().__init__(app, config)

    @abstractmethod
    def _should_skip_auth(self, path: str) -> bool:
        """检查是否需要跳过认证

        Args:
            path: 请求路径

        Returns:
            bool: 是否跳过认证
        """
        pass

    @abstractmethod
    async def authenticate(self, request: Request) -> Optional[Any]:
        """认证方法

        Args:
            request: 请求对象

        Returns:
            认证用户对象,认证失败返回None

        Raises:
            NotImplementedError: 子类未实现该方法
        """
        raise NotImplementedError()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 检查是否需要跳过认证
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        # 进行认证
        user = await self.authenticate(request)
        if user:
            request.state.user = user
            request.state.context = getattr(request.state, "context", {})
            request.state.context["user_id"] = getattr(user, "id", None)

        # 继续处理请求
        return await call_next(request)


class BaseCacheMiddleware(BaseCustomMiddleware):
    """缓存中间件基类

    提供响应缓存的基本功能
    支持多级缓存和缓存策略配置
    """

    async def get_cache_key(self, request: Request) -> str:
        """获取缓存键

        Args:
            request: 请求对象

        Returns:
            缓存键
        """
        return f"{request.method}:{request.url.path}"

    async def get_cached_response(self, key: str) -> Optional[Response]:
        """获取缓存的响应(子类必须实现)

        Args:
            key: 缓存键

        Returns:
            缓存的响应对象,不存在返回None

        Raises:
            NotImplementedError: 子类未实现该方法
        """
        raise NotImplementedError()

    async def cache_response(self, key: str, response: Response, ttl: Optional[int] = None) -> None:
        """缓存响应(子类必须实现)

        Args:
            key: 缓存键
            response: 响应对象
            ttl: 过期时间(秒)

        Raises:
            NotImplementedError: 子类未实现该方法
        """
        raise NotImplementedError()

    async def before_request(self, request: Request) -> None:
        """检查缓存

        Args:
            request: 请求对象
        """
        if not self.config.cache_enabled:
            return

        key = await self.get_cache_key(request)
        cached = await self.get_cached_response(key)
        if cached:
            request.state.cached_response = cached
            request.state.context["cache_hit"] = True

    async def after_response(self, request: Request, response: Response) -> Response:
        """缓存响应

        Args:
            request: 请求对象
            response: 响应对象

        Returns:
            响应对象
        """
        if not self.config.cache_enabled:
            return response

        if hasattr(request.state, "cached_response"):
            return request.state.cached_response

        if self._should_cache_response(request, response):
            key = await self.get_cache_key(request)
            await self.cache_response(key, response, ttl=self.config.cache_ttl)

        return response

    def _should_cache_response(self, request: Request, response: Response) -> bool:
        """判断是否应该缓存响应

        Args:
            request: 请求对象
            response: 响应对象

        Returns:
            是否应该缓存
        """
        return (
            request.method == "GET"
            and response.status_code == 200
            and not any(request.url.path.startswith(path) for path in self.config.exclude_paths)
        )


class BaseLoggingMiddleware(BaseCustomMiddleware):
    """日志记录中间件基类

    提供统一的日志记录功能
    支持请求日志、响应日志、错误日志等
    """

    async def before_request(self, request: Request) -> None:
        """记录请求日志

        Args:
            request: 请求对象
        """
        self.logger.info(
            "收到请求",
            extra={
                "request_id": request.state.request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "user": getattr(request.state, "user", None),
            },
        )

    async def after_response(self, request: Request, response: Response) -> Response:
        """记录响应日志

        Args:
            request: 请求对象
            response: 响应对象

        Returns:
            响应对象
        """
        self.logger.info(
            "发送响应",
            extra={
                "request_id": request.state.request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{time.time() - request.state.start_time:.3f}s",
                "user": getattr(request.state, "user", None),
                "cache_hit": request.state.context.get("cache_hit", False),
            },
        )
        return response

    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """记录异常日志

        Args:
            request: 请求对象
            exc: 异常对象

        Returns:
            错误响应对象

        Raises:
            Exception: 未处理的异常
        """
        self.logger.exception(
            "请求处理异常",
            extra={
                "request_id": request.state.request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(exc),
                "error_type": exc.__class__.__name__,
                "user": getattr(request.state, "user", None),
            },
        )
        raise exc


class BaseTimingMiddleware(BaseCustomMiddleware):
    """请求处理时间统计中间件

    提供请求处理时间的统计功能
    支持慢请求检测和性能分析
    """

    async def after_response(self, request: Request, response: Response) -> Response:
        """记录请求处理时间

        Args:
            request: 请求对象
            response: 响应对象

        Returns:
            响应对象
        """
        process_time = time.time() - request.state.start_time

        # 记录处理时间
        self.logger.info(
            "请求处理完成",
            extra={
                "request_id": request.state.request_id,
                "method": request.method,
                "path": request.url.path,
                "process_time": f"{process_time:.3f}s",
                "slow_request": process_time > 1.0,  # 超过1秒认为是慢请求
                "user": getattr(request.state, "user", None),
            },
        )

        # 添加处理时间响应头
        response.headers["X-Process-Time"] = f"{process_time:.3f}s"

        return response


class BaseRequestIDMiddleware(BaseCustomMiddleware):
    """请求ID中间件

    为每个请求生成唯一标识
    支持请求追踪和日志关联
    """

    async def before_request(self, request: Request) -> None:
        """添加请求ID

        Args:
            request: 请求对象
        """
        request_id = self._get_request_id(request)
        request.headers["X-Request-ID"] = request_id
        request.state.request_id = request_id


class BaseMiddleware(ABC):
    """中间件抽象基类

    所有自定义中间件都应该继承这个基类
    提供请求处理的基本框架
    """

    @abstractmethod
    async def before_request(self, request: Request) -> None:
        """请求处理前的钩子

        Args:
            request: 请求对象
        """
        pass

    @abstractmethod
    async def after_request(self, request: Request, response: Response) -> None:
        """请求处理后的钩子

        Args:
            request: 请求对象
            response: 响应对象
        """
        pass

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """中间件调用方法

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        await self.before_request(request)
        response = await call_next(request)
        await self.after_request(request, response)
        return response


class RequestLoggingMiddleware(BaseMiddleware):
    """请求日志中间件

    记录详细的请求处理日志
    支持性能监控和问题诊断
    """

    async def before_request(self, request: Request) -> None:
        """记录请求开始日志

        Args:
            request: 请求对象
        """
        request.state.start_time = time.time()
        logging.info(f"开始处理请求: {request.method} {request.url.path}")

    async def after_request(self, request: Request, response: Response) -> None:
        """记录请求完成日志

        Args:
            request: 请求对象
            response: 响应对象
        """
        process_time = time.time() - request.state.start_time
        logging.info(
            f"请求处理完成: {request.method} {request.url.path} " f"状态码: {response.status_code} " f"处理时间: {process_time:.3f}s"
        )


class ErrorHandlingMiddleware(BaseMiddleware):
    """统一错误处理中间件

    提供全局的异常处理机制
    支持错误响应格式化和日志记录
    """

    async def before_request(self, request: Request) -> None:
        """请求前处理

        Args:
            request: 请求对象
        """
        pass

    async def after_request(self, request: Request, response: Response) -> None:
        """请求后处理

        Args:
            request: 请求对象
            response: 响应对象
        """
        pass

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """处理请求和异常

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logging.exception("请求处理发生异常")
            return JSONResponse(content={"code": 500, "message": "服务器内部错误", "detail": str(e)}, status_code=500)
