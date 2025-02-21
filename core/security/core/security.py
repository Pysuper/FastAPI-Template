from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.setting import settings
from core.dependencies import async_db
from models.user import User
from utils.security import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api.api_v1_str}/auth/login")


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    query = await db.execute("SELECT * FROM user WHERE email = :email AND is_active = true", {"email": email})
    return query.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """验证用户"""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(db: AsyncSession = Depends(async_db), token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.security_config.SECRET_KEY, algorithms=[settings.security_config.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


def check_permission(required_permission: str):
    """权限检查装饰器"""

    async def permission_dependency(current_user: User = Depends(get_current_user)) -> None:
        if not current_user.has_permission(required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission}",
            )

    return permission_dependency


def check_role(required_role: str):
    """角色检查装饰器"""

    async def role_dependency(current_user: User = Depends(get_current_user)) -> None:
        if not current_user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {required_role}",
            )

    return role_dependency
