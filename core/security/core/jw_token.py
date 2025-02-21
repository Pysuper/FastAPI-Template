# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：jwt.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：JWT工具类
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status

from core.config.setting import settings


class JWTHandler:
    """JWT处理器"""

    ALGORITHM = "HS256"

    @classmethod
    def create_access_token(
        cls, subject: str, expires_delta: Optional[timedelta] = None, claims: Dict[str, Any] = None
    ) -> str:
        """
        创建访问令牌
        :param subject: 令牌主题(通常是用户ID)
        :param expires_delta: 过期时间
        :param claims: 额外的声明
        :return: JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = datetime.utcnow() + expires_delta

        to_encode = {"exp": expire, "sub": str(subject), "iat": datetime.utcnow()}

        if claims:
            to_encode.update(claims)

        return jwt.encode(to_encode, settings.security.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def decode_token(cls, token: str) -> Dict[str, Any]:
        """
        解码并验证token
        :param token: JWT token
        :return: 解码后的数据
        """
        try:
            payload = jwt.decode(token, settings.security.SECRET_KEY, algorithms=[cls.ALGORITHM])

            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


class JWTManager:
    async def init(self):
        pass

    async def close(self):
        pass

    async def reload(self, config):
        pass
