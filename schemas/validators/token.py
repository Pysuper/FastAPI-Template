from datetime import datetime
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from constants.users import TokenType
from core.config.setting import get_settings
from exceptions.http.auth import AuthenticationException

settings = get_settings()


class TokenPayload(BaseModel):
    """令牌载荷"""

    sub: str
    exp: Optional[datetime] = None
    type: Optional[TokenType] = TokenType.ACCESS  # 令牌类型

    @classmethod
    def validate_access_token(cls, token: str) -> "TokenPayload":
        """验证访问令牌"""
        try:
            payload = jwt.decode(
                token,
                settings.security.SECRET_KEY,
                algorithms=[settings.security.ALGORITHM],
            )
            return cls(**payload)
        except JWTError:
            raise AuthenticationException("无效的访问令牌")

    @classmethod
    def validate_refresh_token(cls, token: str) -> "TokenPayload":
        """验证刷新令牌"""
        try:
            payload = jwt.decode(
                token,
                settings.security.SECRET_KEY,
                algorithms=[settings.security.ALGORITHM],
            )
            return cls(**payload)
        except JWTError:
            raise AuthenticationException("无效的刷新令牌")


class TokenResponse(BaseModel):
    """令牌响应"""

    access_token: str
    refresh_token: str 
    token_type: str = "bearer"
    expires_in: int = 3600