"""
统一的缓存中间件实现
"""

import hashlib
import json
from typing import Any, Dict, Optional

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse, PlainTextResponse
from starlette.types import ASGIApp

from core.cache.config.config import CacheConfig
from core.cache.manager import CacheManager
from core.exceptions.system.cache import CacheException
from core.middlewares.base import BaseCacheMiddleware


class CacheMiddleware(BaseCacheMiddleware):
    """统一的缓存中间件实现"""

    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        """初始化中间件

        Args:
            app: ASGI应用
            config: 中间件配置
        """
        super().__init__(app, config)
        self.cache_config = None
        self.cache_manager = None
        self._initialized = False
        print(" ✅ CacheMiddleware")

    async def ensure_initialized(self) -> None:
        """确保中间件已初始化"""
        if not self._initialized:
            await self.initialize()
            self._initialized = True

    async def initialize(self) -> None:
        """初始化缓存配置"""
        try:
            # 获取缓存配置
            cache_config_dict = {
                "backend_type": "redis",
                "strategy": "redis",
                "enable_memory_cache": self.config.cache_enabled,
                "enable_redis_cache": self.config.cache_enabled,
                "enable_stats": True,
                "key_prefix": "cache:",
                "version": "v1",
                "CACHE_TTL": self.config.cache_ttl,
                "redis": {
                    "host": "localhost",
                    "port": your_port,
                    "db": 4,
                    "password": "Affect_PySuper"
                }
            }
            
            # 初始化缓存配置
            self.cache_config = CacheConfig(**cache_config_dict)
            
            # 初始化缓存管理器
            self.cache_manager = CacheManager(
                strategy="redis",
                settings=self.cache_config,
                prefix=self.cache_config.key_prefix,
                default_ttl=self.cache_config.CACHE_TTL
            )
            await self.cache_manager.init(self.cache_config)
            
            self.logger.info("缓存中间件初始化成功")
        except Exception as e:
            self.logger.error(f"缓存中间件初始化失败: {str(e)}")
            raise

    async def get_cached_response(self, key: str) -> Optional[Response]:
        """获取缓存的响应

        Args:
            key: 缓存键

        Returns:
            缓存的响应对象,不存在返回None
        """
        await self.ensure_initialized()
        return await self._get_cached_response(key)

    async def cache_response(self, key: str, response: Response, ttl: Optional[int] = None) -> None:
        """缓存响应

        Args:
            key: 缓存键
            response: 响应对象
            ttl: 过期时间(秒)
        """
        await self.ensure_initialized()
        await self._cache_response(key, response)

    def _should_cache(self, request: Request) -> bool:
        """判断是否需要缓存"""
        if not hasattr(self, 'cache_config') or not self.cache_config or not self.cache_config.enabled:
            return False

        # 不缓存流式响应
        if request.headers.get("accept") == "text/event-stream":
            return False
            
        # 不缓存大文件下载
        if request.headers.get("range"):
            return False

        # 不缓存特定路径
        exclude_paths = [
            "/favicon.ico",  # 不缓存网站图标
            *self.cache_config.exclude_paths
        ]
        if any(request.url.path.startswith(path) for path in exclude_paths):
            return False

        # 只缓存GET和HEAD请求
        if request.method not in ["GET", "HEAD"]:
            return False

        if request.method in self.cache_config.exclude_methods:
            return False

        return True

    def _generate_cache_key(self, request: Request) -> str:
        """生成缓存键"""
        # 基础键
        key_parts = [self.cache_config.prefix, request.method, request.url.path]

        # 添加查询参数
        if self.cache_config.vary_by_query:
            query_params = dict(request.query_params)
            for param in self.cache_config.vary_by_query:
                if param in query_params:
                    key_parts.append(f"{param}={query_params[param]}")
        else:
            key_parts.append(str(request.query_params))

        # 添加请求头
        if self.cache_config.vary_by_headers:
            for header in self.cache_config.vary_by_headers:
                value = request.headers.get(header)
                if value:
                    key_parts.append(f"{header}={value}")

        # 生成最终的缓存键
        key = ":".join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()

    async def _get_cached_response(self, key: str) -> Optional[Response]:
        """获取缓存的响应"""
        try:
            await self.ensure_initialized()
                
            cached_data = await self.cache_manager.get_json(key)
            if cached_data:
                content = cached_data["content"]
                headers = cached_data["headers"]
                
                # 移除可能导致问题的头部
                headers.pop("content-length", None)
                headers.pop("Content-Length", None)
                headers.pop("transfer-encoding", None)
                headers.pop("Transfer-Encoding", None)
                
                # 创建新的响应
                response = Response(
                    content=content,
                    status_code=cached_data["status_code"],
                    headers=headers
                )
                return response
        except Exception as e:
            self.logger.error(f"Error getting cached response: {str(e)}")
        return None

    async def _cache_response(self, key: str, response: Response) -> None:
        """缓存响应"""
        try:
            await self.ensure_initialized()
                
            # 准备缓存数据
            content = None
            
            # 处理不同类型的响应
            if isinstance(response, StreamingResponse):
                # 流式响应不缓存
                return
                
            if hasattr(response, "body") and response.body:
                # 普通响应
                content = response.body.decode() if isinstance(response.body, bytes) else response.body
            elif hasattr(response, "render"):
                # 模板响应
                try:
                    content = await response.render(response.content)
                except Exception as e:
                    self.logger.error(f"Error rendering response: {str(e)}")
                    return
                    
            # 如果没有内容，不缓存
            if content is None:
                return
                
            # 获取并清理头部
            headers = dict(response.headers)
            headers.pop("content-length", None)
            headers.pop("Content-Length", None)
            headers.pop("transfer-encoding", None)
            headers.pop("Transfer-Encoding", None)
            
            cache_data = {
                "content": content,
                "status_code": response.status_code,
                "headers": headers,
            }

            # 使用set_json方法缓存响应
            await self.cache_manager.set_json(
                key, 
                cache_data, 
                expire=self.cache_config.CACHE_TTL
            )
        except Exception as e:
            self.logger.error(f"Error caching response: {str(e)}")
            
    def _add_cache_headers(self, response: Response, cache_hit: bool = False) -> None:
        """添加缓存相关的响应头"""
        response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
        response.headers["Cache-Control"] = f"max-age={self.cache_config.CACHE_TTL}"

    async def process_request(self, request: Request) -> None:
        """处理请求"""
        await self.ensure_initialized()
        
        if not self._should_cache(request):
            return

        # 生成缓存键
        cache_key = self._generate_cache_key(request)
        request.state.cache_key = cache_key

        # 尝试获取缓存的响应
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            request.state.cached_response = cached_response

    async def process_response(self, request: Request, response: Response) -> Response:
        """处理响应"""
        await self.ensure_initialized()
        
        # 不缓存错误响应
        if response.status_code >= 400:
            return response
            
        if not self._should_cache(request):
            return response

        # 不缓存流式响应
        if isinstance(response, StreamingResponse):
            return response

        # 如果有缓存响应，直接返回
        if hasattr(request.state, "cached_response"):
            cached_response = request.state.cached_response
            self._add_cache_headers(cached_response, cache_hit=True)
            return cached_response

        # 缓存新的响应
        try:
            cache_key = getattr(request.state, "cache_key", None)
            if cache_key:
                await self._cache_response(cache_key, response)
                self._add_cache_headers(response, cache_hit=False)
        except Exception as e:
            self.logger.error(f"Error in process_response: {str(e)}")

        return response

    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """处理异常"""
        from starlette.exceptions import HTTPException
        from starlette.responses import JSONResponse, Response, PlainTextResponse
        from starlette.status import (
            HTTP_404_NOT_FOUND,
            HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        try:
            if isinstance(exc, HTTPException):
                # 处理HTTP异常
                status_code = exc.status_code
                headers = getattr(exc, "headers", {}) or {}
                
                if status_code == HTTP_404_NOT_FOUND:
                    if request.url.path == "/favicon.ico":
                        # 对于favicon.ico的404请求，返回空响应
                        return PlainTextResponse(
                            content="",
                            status_code=status_code,
                            headers=headers,
                            media_type="image/x-icon"
                        )
                
                # 其他HTTP异常返回JSON响应
                content = {
                    "code": status_code,
                    "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
                    "data": None
                }
                
                return JSONResponse(
                    status_code=status_code,
                    content=content,
                    headers=headers
                )
                
            elif isinstance(exc, CacheException):
                # 记录缓存错误但不影响请求处理
                self.logger.error(
                    "Cache middleware error",
                    exc_info=True,
                    extra={
                        "error": str(exc),
                        "error_type": exc.__class__.__name__,
                        "cache_key": getattr(request.state, "cache_key", None),
                        **self._get_request_context(request),
                    },
                )
                return await super().handle_exception(request, exc)
                
            else:
                # 其他异常返回500错误
                self.logger.error(
                    "Unhandled exception",
                    exc_info=True,
                    extra={
                        "error": str(exc),
                        "error_type": exc.__class__.__name__,
                        **self._get_request_context(request),
                    },
                )
                return JSONResponse(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "code": HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "Internal Server Error",
                        "data": None
                    }
                )
        except Exception as e:
            # 确保异常处理器本身的错误不会导致500错误
            self.logger.error(f"Error in exception handler: {str(e)}", exc_info=True)
            return PlainTextResponse(
                content="Internal Server Error",
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )


class MemoryCacheMiddleware(BaseCacheMiddleware):
    """内存缓存中间件"""

    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app, config)
        self._cache: Dict[str, Response] = {}

    async def get_cached_response(self, key: str) -> Optional[Response]:
        """获取缓存的响应

        Args:
            key: 缓存键

        Returns:
            缓存的响应对象,不存在返回None
        """
        return self._cache.get(key)

    async def cache_response(self, key: str, response: Response, ttl: Optional[int] = None) -> None:
        """缓存响应

        Args:
            key: 缓存键
            response: 响应对象
            ttl: 过期时间(秒)
        """
        self._cache[key] = response
