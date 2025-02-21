from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.manager import config_manager
from core.config.setting import settings
from core.dependencies.db import async_db, sync_db
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(db: AsyncSession = Depends(async_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    获取当前用户
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        security_config = settings.security
        if not security_config:
            raise ValueError("Security configuration not found")

        payload = jwt.decode(token, security_config.SECRET_KEY, algorithms=[security_config.ALGORITHM])
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError) as e:
        raise credentials_exception from e

    # 使用简单的查询
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    try:
        user = result.scalar_one_or_none()
    except Exception as e:
        print(f"Error getting user: {e}")
        user = None

    if user is None:
        raise credentials_exception

    return user


# from typing import Optional
#
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
#
# from exceptions.base import AuthenticationException
# from security.auth.base_security import SecurityManager
#
# security = HTTPBearer()
# security_manager = SecurityManager()
# async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = None):
#     """获取当前用户"""
#     if not credentials:
#         raise AuthenticationException("Not authenticated")
#
#     token = credentials.credentials
#     user_id = security_manager.decode_token(token)
#
#     if not user_id:
#         raise AuthenticationException("Invalid token or expired")
#
#     return user_id


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前超级用户
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def get_oauth2_scheme() -> OAuth2PasswordBearer:
    """获取OAuth2认证方案"""
    app_config = config_manager.get("app")
    if not app_config:
        raise ValueError("Application configuration not found")
    return OAuth2PasswordBearer(tokenUrl=f"{app_config.api_v1_str}/auth/login")


oauth2_scheme = Depends(get_oauth2_scheme)


async def is_admin(current_user: User = Depends(get_current_user)) -> bool:
    """
    判断当前用户是否是管理员
    """
    return current_user.is_superuser
