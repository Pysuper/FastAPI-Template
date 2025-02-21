"""
@Project ：Speedy 
@File    ：encryption.py
@Author  ：PySuper
@Date    ：2024-12-28 02:36
@Desc    ：加密中间件

提供请求和响应的加密处理功能，包括：
    - 敏感数据加密
    - 响应数据加密
    - 请求数据解密
    - 配置加密
"""

from typing import Any, Dict, Optional, Set
import json

from fastapi import Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from cache.exceptions import EncryptionError
from core.security.core.encryption import EncryptionProvider
from core.loge.manager import logic as logger

class EncryptionMiddleware(BaseHTTPMiddleware):
    """加密中间件"""

    def __init__(
        self,
        app: ASGIApp,
        secret_key: Optional[str] = None,
        sensitive_fields: Optional[Set[str]] = None,
        exclude_paths: Optional[Set[str]] = None,
    ) -> None:
        """
        初始化加密中间件
        :param app: ASGI应用
        :param secret_key: 加密密钥
        :param sensitive_fields: 敏感字段集合
        :param exclude_paths: 排除路径集合
        """
        super().__init__(app)
        self.encryption_provider = EncryptionProvider()
        self.sensitive_fields = sensitive_fields or set()
        self.exclude_paths = exclude_paths or {"/docs", "/redoc", "/openapi.json"}

        print(" ✅ EncryptionMiddleware")

    def _should_process(self, request: Request) -> bool:
        """
        判断是否需要处理该请求
        :param request: 请求对象
        :return: 是否需要处理
        """
        return request.url.path not in self.exclude_paths

    async def _process_request_body(self, request: Request) -> Dict[str, Any]:
        """
        处理请求体
        :param request: 请求对象
        :return: 处理后的请求体
        """
        try:
            # 先读取原始body
            body_bytes = await request.body()
            
            # 保存原始body以供后续使用
            async def receive():
                return {"type": "http.request", "body": body_bytes, "more_body": False}
            
            request._receive = receive
            
            if not body_bytes:
                return {}
            
            body = json.loads(body_bytes.decode())
            if isinstance(body, dict):
                return await self.encryption_provider.decrypt_dict(body, self.sensitive_fields)
            return body
        except json.JSONDecodeError:
            logger.warning("请求体不是有效的JSON", extra={"path": request.url.path})
            return {}
        except Exception as e:
            logger.error("处理请求体失败", extra={"error": str(e), "path": request.url.path})
            raise EncryptionError(f"请求体处理失败: {str(e)}")

    async def _process_response_body(self, response: Response) -> Any:
        """
        处理响应体
        :param response: 响应对象
        :return: 处理后的响应体
        """
        try:
            # 如果是 StreamingResponse，直接返回
            if isinstance(response, StreamingResponse):
                return response
                
            # 处理 JSON 响应
            if isinstance(response, JSONResponse):
                body = response.body
                if isinstance(body, bytes):
                    body = json.loads(body.decode('utf-8'))
                if isinstance(body, dict):
                    encrypted_body = await self.encryption_provider.encrypt_dict(body, self.sensitive_fields)
                    return JSONResponse(content=encrypted_body)
            
            # 处理其他类型响应
            return response
        except Exception as e:
            logger.error("响应加密失败", extra={"error": str(e)})
            raise EncryptionError(f"响应加密失败: {str(e)}")

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        处理请求和响应
        :param request: 请求对象
        :param call_next: 下一个处理函数
        :return: 响应对象
        """
        if not self._should_process(request):
            # logger.debug(f"跳过加密处理: {request.url.path}")
            return await call_next(request)
        
        try:
            # logger.debug(f"开始处理请求: {request.url.path}")
            
            # 处理请求体
            if request.method in {"POST", "PUT", "PATCH"}:
                # logger.debug("开始处理请求体")
                decrypted_body = await self._process_request_body(request)
                request.state.body = decrypted_body
                # logger.debug("请求体处理完成")
            
            # 处理响应
            response = await call_next(request)
            # logger.debug("开始处理响应")
            
            # 处理响应体
            processed_response = await self._process_response_body(response)
            # logger.debug("响应处理完成")
            
            return processed_response
        
        except Exception as e:
            logger.error(
                "加密中间件处理失败", extra={
                    "error": str(e),
                    "path": request.url.path,
                    "method": request.method,
                    "headers": dict(request.headers)
                    }
                )
            raise EncryptionError(f"加密中间件处理失败: {str(e)}")
