# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：auth.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：认证后端
"""
from typing import Optional, Tuple

from starlette.authentication import AuthenticationBackend, AuthCredentials, BaseUser
from starlette.requests import Request

from security.core.jw_token import JWTHandler
from models.user import User


class AuthProvider(AuthenticationBackend):
    """认证后端"""

    async def authenticate(self, request: Request) -> Optional[Tuple[AuthCredentials, BaseUser]]:
        if "Authorization" not in request.headers:
            return None

        auth = request.headers["Authorization"]
        try:
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                return None

            # 验证token
            payload = JWTHandler.decode_token(token)

            # 创建用户实例
            user = User(payload)

            # 构建认证凭据
            scopes = ["authenticated"]
            scopes.extend(user.roles)
            scopes.extend(user.permissions)

            return AuthCredentials(scopes), user

        except Exception:
            return None

    async def init(self):
        pass

    async def close(self):
        pass

    async def reload(self, config):
        pass
