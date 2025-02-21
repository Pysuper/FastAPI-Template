# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：auth.py
@Author  ：PySuper
@Date    ：2024/12/24 17:13 
@Desc    ：认证中间件

提供认证相关的功能，包括：
    - JWT认证
    - 令牌验证
    - 用户认证
    - 权限验证
"""

from typing import Dict, Any, Optional

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette.requests import Request
from starlette.types import ASGIApp
from schemas.base.response import Response, JSONResponse, RequestResponseEndpoint

from core.config.setting import settings
from exceptions.http.auth import AuthenticationException
from core.security.core.exceptions import AuthenticationError
from core.middlewares.base import BaseAuthMiddleware
from security.manager import security_manager
from core.loge.logger import CustomLogger


class AuthMiddleware(BaseAuthMiddleware):
    """认证中间件"""

    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化认证中间件
        :param app: ASGI应用
        :param config: 中间件配置
        """
        super().__init__(app, config)
        self.exclude_paths = settings.security.AUTH_EXCLUDE_PATHS or []
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.logger = CustomLogger("auth")
        print(" ✅ AuthMiddleware")

    def _should_skip_auth(self, path: str) -> bool:
        """
        检查是否需要跳过认证
        :param path: 请求路径
        :return: 是否跳过认证
        """
        # 基础公开路径
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/health",
            "/metrics",
            "/favicon.ico",
            "/static",
            "/",
        ]
        
        # 添加配置中的排除路径
        skip_paths.extend(self.exclude_paths)
        
        # 检查路径是否需要跳过
        return any(path.startswith(skip_path) for skip_path in skip_paths)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        处理请求
        :param request: 请求对象
        :param call_next: 下一个处理函数
        :return: 响应对象
        """
        # 检查是否需要跳过认证
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        try:
            # 进行认证
            user = await self.authenticate(request)
            request.state.user = user
            self.logger.info_with_extra(
                "认证成功",
                extra_fields={
                    "user_id": user,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            return await call_next(request)
        except AuthenticationException as e:
            self.logger.error(
                "认证失败",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None
                }
            )
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)}
            )
        except Exception as e:
            self.logger.error_with_extra(
                "认证中间件处理失败",
                extra_fields={
                    "error": str(e),
                    "path": request.url.path,
                    "method": request.method
                },
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

    async def authenticate(self, request: Request) -> dict:
        """
        认证方法
        :param request: 请求对象
        :return: 用户信息
        :raises AuthenticationError: 当认证失败时
        """
        try:
            # 获取认证信息
            auth = request.headers.get("Authorization")
            if not auth:
                raise AuthenticationException("Missing authorization header")

            # 验证token
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                raise AuthenticationException("Invalid authentication scheme")

            # 解析token
            user_id = await security_manager.decode_token(token)
            if not user_id:
                raise AuthenticationException("Invalid token or expired")

            return user_id

        except AuthenticationException as e:
            raise e
        except Exception as e:
            self.logger.error_with_extra(
                "Token验证失败",
                extra_fields={
                    "error": str(e),
                    "path": request.url.path,
                    "method": request.method
                },
                exc_info=True
            )
            raise AuthenticationException(str(e))
