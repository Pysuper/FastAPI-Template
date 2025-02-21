import gzip
import zlib
from typing import List, Optional

import brotli
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp

from core.config.setting import settings
from core.middlewares.base import BaseCustomMiddleware


class CompressionConfig:
    """压缩配置类"""

    def __init__(
        self,
        minimum_size: int = 500,  # 最小压缩大小(字节)
        compression_level: int = 6,  # 压缩级别(1-9)
        include_media_types: List[str] = [  # 需要压缩的媒体类型
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/json",
            "application/xml",
        ],
        exclude_paths: List[str] = ["/health", "/metrics"],
        algorithms: List[str] = ["br", "gzip", "deflate"],  # 支持的压缩算法
    ):
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.include_media_types = include_media_types
        self.exclude_paths = exclude_paths
        self.algorithms = algorithms


class CompressionMiddleware(BaseCustomMiddleware):
    """压缩中间件"""

    def initialize(self) -> None:
        """初始化压缩配置"""
        compression_config = self.config.get("compression", {})
        self.compression_config = CompressionConfig(**compression_config)

    async def process_request(self, request: Request) -> None:
        """处理请求"""
        if not self._should_process(request):
            return

        # 记录客户端支持的压缩算法
        accept_encoding = request.headers.get("accept-encoding", "")
        request.state.supported_compressions = [
            algo for algo in self.compression_config.algorithms if algo in accept_encoding.lower()
        ]

    async def process_response(self, request: Request, response: Response) -> Response:
        """处理响应"""
        if not self._should_process(request):
            return response

        # 检查是否需要压缩
        if not self._should_compress(request, response):
            return response

        # 获取最佳压缩算法
        compression = self._get_best_compression(request)
        if not compression:
            return response

        # 压缩响应体
        try:
            compressed_body = self._compress_body(response.body, compression, self.compression_config.compression_level)

            # 如果压缩后的大小更大，则返回原始响应
            if len(compressed_body) >= len(response.body):
                return response

            # 更新响应
            response.body = compressed_body
            response.headers["Content-Encoding"] = compression
            response.headers["Content-Length"] = str(len(compressed_body))
            response.headers["Vary"] = "Accept-Encoding"

        except Exception as e:
            self.logger.error(
                f"Compression failed: {str(e)}",
                extra={"compression": compression, **self._get_request_context(request)},
            )

        return response

    def _should_compress(self, request: Request, response: Response) -> bool:
        """检查是否需要压缩"""
        # 检查响应体大小
        if not hasattr(response, "body") or len(response.body) < self.compression_config.minimum_size:
            return False

        # 检查内容类型
        content_type = response.headers.get("content-type", "").lower()
        if not any(media_type in content_type for media_type in self.compression_config.include_media_types):
            return False

        # 检查是否已经压缩
        if "content-encoding" in response.headers:
            return False

        return True

    def _get_best_compression(self, request: Request) -> Optional[str]:
        """获取最佳压缩算法"""
        supported = getattr(request.state, "supported_compressions", [])
        for algo in self.compression_config.algorithms:
            if algo in supported:
                return algo
        return None

    def _compress_body(self, body: bytes, algorithm: str, level: int) -> bytes:
        """压缩响应体"""
        if algorithm == "br":
            return brotli.compress(body, quality=level)
        elif algorithm == "gzip":
            return gzip.compress(body, compresslevel=level)
        elif algorithm == "deflate":
            return zlib.compress(body, level=level)
        return body

    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """处理异常"""
        self.logger.error(
            "Compression failed",
            exc_info=True,
            extra={
                "compression": getattr(request.state, "supported_compressions", []),
                **self._get_request_context(request),
            },
        )
        return await super().handle_exception(request, exc)


class CompressionMiddleware(BaseCustomMiddleware):
    """
    压缩中间件
    处理响应压缩
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.min_size = settings.middleware.compression_min_size or 1024  # 最小压缩大小
        self.compressible_types = settings.middleware.compression_types or [
            "text/",
            "application/json",
            "application/xml",
            "application/javascript",
            "application/x-javascript",
            "text/javascript",
        ]
        print(" ✅ CompressionMiddleware")

    def _should_compress(self, request: Request, response: Response) -> bool:
        """判断是否需要压缩"""
        # 检查Accept-Encoding
        accept_encoding = request.headers.get("Accept-Encoding", "").lower()
        if "gzip" not in accept_encoding and "deflate" not in accept_encoding:
            return False

        # 检查Content-Type
        content_type = response.headers.get("Content-Type", "")
        if not any(t in content_type for t in self.compressible_types):
            return False

        # 检查Content-Length
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) < self.min_size:
            return False

        return True

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # 如果是StreamingResponse,直接返回
        if isinstance(response, StreamingResponse):
            return response

        if not self._should_compress(request, response):
            return response

        # 获取原始内容
        content = await response.body()

        # 根据Accept-Encoding选择压缩方法
        accept_encoding = request.headers.get("Accept-Encoding", "").lower()
        if "gzip" in accept_encoding:
            compressed = gzip.compress(content)
            response.headers["Content-Encoding"] = "gzip"
        elif "deflate" in accept_encoding:
            compressed = zlib.compress(content)
            response.headers["Content-Encoding"] = "deflate"
        else:
            return response

        # 更新响应
        response.headers["Content-Length"] = str(len(compressed))
        response.body = compressed
        return response
