from functools import wraps
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from exceptions.http.auth import AuthorizationException
from models.user import User


def require_permissions(permissions: List[str]):
    """
    检查用户是否具有所需权限的装饰器
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和数据库会话
            db = kwargs.get("db") or next((arg for arg in args if isinstance(arg, Session)), None)
            current_user = kwargs.get("current_user") or next((arg for arg in args if isinstance(arg, User)), None)

            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

            # 检查用户权限
            user_permissions = set()
            for role in current_user.roles:
                for permission in role.permissions:
                    user_permissions.add(permission.name)

            if not all(perm in user_permissions for perm in permissions):
                raise AuthorizationException("没有足够的权限执行此操作")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_roles(roles: List[str]):
    """
    检查用户是否具有所需角色的装饰器
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和数据库会话
            db = kwargs.get("db") or next((arg for arg in args if isinstance(arg, Session)), None)
            current_user = kwargs.get("current_user") or next((arg for arg in args if isinstance(arg, User)), None)

            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

            # 检查用户角色
            user_roles = {role.name for role in current_user.roles}
            if not any(role in user_roles for role in roles):
                raise AuthorizationException("没有足够的角色执行此操作")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def data_permission(resource: str, action: Optional[str] = None):
    """
    数据权限检查装饰器
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和数据库会话
            db = kwargs.get("db") or next((arg for arg in args if isinstance(arg, Session)), None)
            current_user = kwargs.get("current_user") or next((arg for arg in args if isinstance(arg, User)), None)

            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error",
                )

            # 检查数据权限
            user_permissions = set()
            for role in current_user.roles:
                for permission in role.permissions:
                    if permission.resource == resource:
                        if not action or permission.action == action:
                            user_permissions.add(f"{permission.resource}:{permission.action}")

            if not user_permissions:
                raise AuthorizationException("没有足够的数据权限执行此操作")

            return await func(*args, **kwargs)

        return wrapper

    return decorator
