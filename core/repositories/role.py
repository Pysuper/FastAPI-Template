"""
角色数据访问层
实现角色相关的所有数据库操作
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Permission, Role, User
from core.repositories import BaseRepository
from schemas.validators.rbac import RoleCreate, RoleUpdate


class RoleRepository(BaseRepository[Role, RoleCreate, RoleUpdate]):
    """
    角色仓储类
    实现角色特定的数据库操作
    """

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Role]:
        """
        通过名称获取角色
        """
        query = select(Role).where(Role.name == name, Role.is_deleted == False)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_roles(self, db: AsyncSession, *, user_id: int) -> List[Role]:
        """
        获取用户的所有角色
        """
        query = select(Role).join(Role.users).where(User.id == user_id, Role.is_deleted == False)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_role_permissions(self, db: AsyncSession, *, role_id: int) -> List[Permission]:
        """
        获取角色的所有权限
        """
        query = select(Permission).join(Permission.roles).where(Role.id == role_id, Permission.is_deleted == False)
        result = await db.execute(query)
        return result.scalars().all()

    async def add_permission(self, db: AsyncSession, *, role_id: int, permission_id: int) -> Optional[Role]:
        """
        为角色添加权限
        """
        role = await self.get(db, id=role_id)
        if not role:
            return None

        permission = await db.get(Permission, permission_id)
        if not permission:
            return None

        role.permissions.append(permission)
        await db.commit()
        await db.refresh(role)
        return role

    async def remove_permission(self, db: AsyncSession, *, role_id: int, permission_id: int) -> Optional[Role]:
        """
        移除角色的权限
        """
        role = await self.get(db, id=role_id)
        if not role:
            return None

        permission = await db.get(Permission, permission_id)
        if not permission:
            return None

        role.permissions.remove(permission)
        await db.commit()
        await db.refresh(role)
        return role

    async def add_user(self, db: AsyncSession, *, role_id: int, user_id: int) -> Optional[Role]:
        """
        为角色添加用户
        """
        role = await self.get(db, id=role_id)
        if not role:
            return None

        user = await db.get(User, user_id)
        if not user:
            return None

        role.users.append(user)
        await db.commit()
        await db.refresh(role)
        return role

    async def remove_user(self, db: AsyncSession, *, role_id: int, user_id: int) -> Optional[Role]:
        """
        移除角色中的用户
        """
        role = await self.get(db, id=role_id)
        if not role:
            return None

        user = await db.get(User, user_id)
        if not user:
            return None

        role.users.remove(user)
        await db.commit()
        await db.refresh(role)
        return role


# 创建角色仓储实例
role_repository = RoleRepository(Role)
