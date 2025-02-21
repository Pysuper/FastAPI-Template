# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：permissions.py
@Author  ：PySuper
@Date    ：2025/1/3 11:55 
@Desc    ：权限管理模块

提供基于RBAC的权限管理功能
支持角色、权限的分配和校验
"""
from functools import wraps
from typing import List, Callable

from fastapi import HTTPException, Depends, status

from core.dependencies import async_db, get_current_user
from services.auth import PermissionService
from sqlalchemy.orm import Session

from models.permission import Permission
from models.role import Role
from models.user import User


def requires_permissions(permissions: List[str], require_all: bool = True) -> Callable:
    """权限校验装饰器

    Args:
        permissions: 需要的权限列表
        require_all: 是否需要满足所有权限,默认为True

    Returns:
        装饰器函数

    Examples:
        >>> @requires_permissions(["view_users"])
        >>> async def get_users():
        >>>     pass

        >>> @requires_permissions(["edit_users", "delete_users"], require_all=False)
        >>> async def manage_users():
        >>>     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args, db: Session = Depends(async_db), current_user: User = Depends(get_current_user), **kwargs
        ):
            # 检查用户是否已认证
            if not current_user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证的用户")

            try:
                # 获取用户的所有权限
                user_permissions = await PermissionService.get_user_permissions(db, current_user.id)
                user_permission_codes = {p.code for p in user_permissions}

                # 检查是否有超级管理员权限
                if "super_admin" in user_permission_codes:
                    return await func(*args, **kwargs)

                # 检查具体权限
                if require_all:
                    # 需要满足所有权限
                    if not all(p in user_permission_codes for p in permissions):
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
                else:
                    # 满足任一权限即可
                    if not any(p in user_permission_codes for p in permissions):
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

                return await func(*args, **kwargs)

            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"权限校验失败: {str(e)}")

        return wrapper

    return decorator


def check_permission(user: User, permission: str, db: Session) -> bool:
    """检查用户是否拥有指定权限

    Args:
        user: 用户对象
        permission: 权限代码
        db: 数据库会话

    Returns:
        bool: 是否拥有权限

    Examples:
        >>> user = get_current_user()
        >>> has_permission = check_permission(user, "view_users", db)
    """
    try:
        # 获取用户的所有权限
        user_permissions = PermissionService.get_user_permissions_sync(db, user.id)
        user_permission_codes = {p.code for p in user_permissions}

        # 检查是否有超级管理员权限
        if "super_admin" in user_permission_codes:
            return True

        # 检查具体权限
        return permission in user_permission_codes

    except Exception:
        return False


def get_user_permissions(user: User, db: Session) -> List[Permission]:
    """获取用户的所有权限

    Args:
        user: 用户对象
        db: 数据库会话

    Returns:
        List[Permission]: 权限列表

    Examples:
        >>> user = get_current_user()
        >>> permissions = get_user_permissions(user, db)
    """
    try:
        return PermissionService.get_user_permissions_sync(db, user.id)
    except Exception:
        return []


def get_user_roles(user: User, db: Session) -> List[Role]:
    """获取用户的所有角色

    Args:
        user: 用户对象
        db: 数据库会话

    Returns:
        List[Role]: 角色列表

    Examples:
        >>> user = get_current_user()
        >>> roles = get_user_roles(user, db)
    """
    try:
        return PermissionService.get_user_roles_sync(db, user.id)
    except Exception:
        return []


def has_role(user: User, role: str, db: Session) -> bool:
    """检查用户是否拥有指定角色

    Args:
        user: 用户对象
        role: 角色代码
        db: 数据库会话

    Returns:
        bool: 是否拥有角色

    Examples:
        >>> user = get_current_user()
        >>> is_admin = has_role(user, "admin", db)
    """
    try:
        # 获取用户的所有角色
        user_roles = PermissionService.get_user_roles_sync(db, user.id)
        user_role_codes = {r.code for r in user_roles}

        # 检查是否有超级管理员角色
        if "super_admin" in user_role_codes:
            return True

        # 检查具体角色
        return role in user_role_codes

    except Exception:
        return False


def requires_roles(roles: List[str], require_all: bool = True) -> Callable:
    """角色校验装饰器

    Args:
        roles: 需要的角色列表
        require_all: 是否需要满足所有角色,默认为True

    Returns:
        装饰器函数

    Examples:
        >>> @requires_roles(["admin"])
        >>> async def admin_only():
        >>>     pass

        >>> @requires_roles(["teacher", "student"], require_all=False)
        >>> async def teacher_or_student():
        >>>     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args, db: Session = Depends(async_db), current_user: User = Depends(get_current_user), **kwargs
        ):
            # 检查用户是否已认证
            if not current_user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证的用户")

            try:
                # 获取用户的所有角色
                user_roles = await PermissionService.get_user_roles(db, current_user.id)
                user_role_codes = {r.code for r in user_roles}

                # 检查是否有超级管理员角色
                if "super_admin" in user_role_codes:
                    return await func(*args, **kwargs)

                # 检查具体角色
                if require_all:
                    # 需要满足所有角色
                    if not all(r in user_role_codes for r in roles):
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="角色不足")
                else:
                    # 满足任一角色即可
                    if not any(r in user_role_codes for r in roles):
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="角色不足")

                return await func(*args, **kwargs)

            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"角色校验失败: {str(e)}")

        return wrapper

    return decorator
