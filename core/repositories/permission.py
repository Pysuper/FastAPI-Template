"""
权限数据访问层
实现权限相关的所有数据库操作
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories import BaseRepository
from schemas.validators.rbac import PermissionCreate, PermissionUpdate
from models import Permission, Role, User


class PermissionRepository(BaseRepository[Permission, PermissionCreate, PermissionUpdate]):
    """
    权限仓储类
    实现权限特定的数据库操作
    """

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Permission]:
        """
        通过名称获取权限
        """
        query = select(Permission).where(
            Permission.name == name,
            Permission.is_deleted == False,
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_resource_action(
        self,
        db: AsyncSession,
        *,
        resource: str,
        action: str,
    ) -> Optional[Permission]:
        """
        通过资源和操作获取权限
        """
        query = select(Permission).where(
            Permission.resource == resource,
            Permission.action == action,
            Permission.is_deleted == False,
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_role_permissions(
        self,
        db: AsyncSession,
        *,
        role_id: int,
    ) -> List[Permission]:
        """
        获取角色的所有权限
        """
        query = (
            select(Permission)
            .join(Permission.roles)
            .where(
                Role.id == role_id,
                Permission.is_deleted == False,
            )
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_user_permissions(
        self,
        db: AsyncSession,
        *,
        user_id: int,
    ) -> List[Permission]:
        """
        获取用户的所有权限（通过角色）
        """
        query = (
            select(Permission)
            .join(Permission.roles)
            .join(Role.users)
            .where(User.id == user_id, Permission.is_deleted == False)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def check_permission(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        resource: str,
        action: str,
    ) -> bool:
        """
        检查用户是否有特定权限
        """
        query = (
            select(Permission)
            .join(Permission.roles)
            .join(Role.users)
            .where(
                User.id == user_id,
                Permission.resource == resource,
                Permission.action == action,
                Permission.is_deleted == False,
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def batch_create_permissions(
        self, db: AsyncSession, *, permissions: List[PermissionCreate]
    ) -> List[Permission]:
        """
        批量创建权限
        """
        db_objs = []
        for perm in permissions:
            db_obj = Permission(
                name=perm.name,
                description=perm.description,
                resource=perm.resource,
                action=perm.action,
            )
            db.add(db_obj)
            db_objs.append(db_obj)

        await db.commit()
        for obj in db_objs:
            await db.refresh(obj)
        return db_objs


# 创建权限仓储实例
permission_repository = PermissionRepository(Permission)
