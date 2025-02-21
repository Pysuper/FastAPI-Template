from typing import List, Optional

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api.base.crud import NotFoundError
from db.metrics.pagination import PaginationParams
from core.repositories import role_repository, permission_repository
from models import Role, Permission
from schemas.validators.rbac import (
    RoleCreate,
    RoleUpdate,
    PermissionCreate,
    PermissionUpdate,
)


class RBACService:
    @staticmethod
    async def create_role(
        db: AsyncSession,
        *,
        role_in: RoleCreate,
        permission_ids: Optional[List[int]] = None,
    ) -> Role:
        """创建角色"""
        # 检查角色名是否已存在
        if await role_repository.get_by_name(db, name=role_in.name):
            raise ValidationError("角色名已存在")

        # 创建角色
        role = await role_repository.create(db, obj_in=role_in)

        # 分配权限
        if permission_ids:
            for permission_id in permission_ids:
                await role_repository.add_permission(
                    db,
                    role_id=role.id,
                    permission_id=permission_id,
                )

        return role

    @staticmethod
    async def update_role(
        db: AsyncSession,
        *,
        role_id: int,
        role_in: RoleUpdate,
        permission_ids: Optional[List[int]] = None,
    ) -> Role:
        """更新角色"""
        # 获取角色
        role = await role_repository.get(db, id=role_id)
        if not role:
            raise NotFoundError("角色不存在")

        # 检查角色名是否已存在
        if role_in.name and role_in.name != role.name:
            if await role_repository.get_by_name(db, name=role_in.name):
                raise ValidationError("角色名已存在")

        # 更新角色
        role = await role_repository.update(db, db_obj=role, obj_in=role_in)

        # 更新权限
        if permission_ids is not None:
            # 获取当前权限
            current_permissions = await role_repository.get_role_permissions(db, role_id=role.id)
            current_permission_ids = {p.id for p in current_permissions}

            # 需要添加的权限
            to_add = set(permission_ids) - current_permission_ids
            for permission_id in to_add:
                await role_repository.add_permission(db, role_id=role.id, permission_id=permission_id)

            # 需要移除的权限
            to_remove = current_permission_ids - set(permission_ids)
            for permission_id in to_remove:
                await role_repository.remove_permission(db, role_id=role.id, permission_id=permission_id)

        return role

    @staticmethod
    async def delete_role(db: AsyncSession, *, role_id: int) -> Role:
        """删除角色"""
        role = await role_repository.get(db, id=role_id)
        if not role:
            raise NotFoundError("角色不存在")
        return await role_repository.remove(db, id=role_id)

    @staticmethod
    async def get_roles(
        db: AsyncSession,
        *,
        pagination: PaginationParams,
        name: Optional[str] = None,
    ) -> tuple[List[Role], int]:
        """获取角色列表"""
        filters = {}
        if name:
            filters["name"] = name
        return await role_repository.get_multi(db, pagination=pagination, **filters)

    @staticmethod
    async def create_permission(
        db: AsyncSession,
        *,
        permission_in: PermissionCreate,
    ) -> Permission:
        """创建权限"""
        # 检查权限名是否已存在
        if await permission_repository.get_by_name(db, name=permission_in.name):
            raise ValidationError("权限名已存在")

        # 检查资源和操作组合是否已存在
        if await permission_repository.get_by_resource_action(
            db, resource=permission_in.resource, action=permission_in.action
        ):
            raise ValidationError("该资源的操作权限已存在")

        return await permission_repository.create(db, obj_in=permission_in)

    @staticmethod
    async def update_permission(
        db: AsyncSession,
        *,
        permission_id: int,
        permission_in: PermissionUpdate,
    ) -> Permission:
        """更新权限"""
        # 获取权限
        permission = await permission_repository.get(db, id=permission_id)
        if not permission:
            raise NotFoundError("权限不存在")

        # 检查权限名是否已存在
        if permission_in.name and permission_in.name != permission.name:
            if await permission_repository.get_by_name(db, name=permission_in.name):
                raise ValidationError("权限名已存在")

        # 检查资源和操作组合是否已存在
        if (permission_in.resource and permission_in.resource != permission.resource) or (
            permission_in.action and permission_in.action != permission.action
        ):
            if await permission_repository.get_by_resource_action(
                db,
                resource=permission_in.resource or permission.resource,
                action=permission_in.action or permission.action,
            ):
                raise ValidationError("该资源的操作权限已存在")

        return await permission_repository.update(db, db_obj=permission, obj_in=permission_in)

    @staticmethod
    async def delete_permission(db: AsyncSession, *, permission_id: int) -> Permission:
        """删除权限"""
        permission = await permission_repository.get(db, id=permission_id)
        if not permission:
            raise NotFoundError("权限不存在")
        return await permission_repository.remove(db, id=permission_id)

    @staticmethod
    async def get_permissions(
        db: AsyncSession,
        *,
        pagination: PaginationParams,
        resource: Optional[str] = None,
        action: Optional[str] = None,
    ) -> tuple[List[Permission], int]:
        """获取权限列表"""
        filters = {}
        if resource:
            filters["resource"] = resource
        if action:
            filters["action"] = action
        return await permission_repository.get_multi(db, pagination=pagination, **filters)

    @staticmethod
    async def assign_role_to_user(db: AsyncSession, *, user_id: int, role_id: int) -> Role:
        """为用户分配角色"""
        role = await role_repository.add_user(db, role_id=role_id, user_id=user_id)
        if not role:
            raise NotFoundError("角色或用户不存在")
        return role

    @staticmethod
    async def remove_role_from_user(db: AsyncSession, *, user_id: int, role_id: int) -> Role:
        """移除用户的角色"""
        role = await role_repository.remove_user(db, role_id=role_id, user_id=user_id)
        if not role:
            raise NotFoundError("角色或用户不存在")
        return role

    @staticmethod
    async def get_user_roles(db: AsyncSession, *, user_id: int) -> List[Role]:
        """获取用户的角色列表"""
        return await role_repository.get_user_roles(db, user_id=user_id)

    @staticmethod
    async def get_user_permissions(db: AsyncSession, *, user_id: int) -> List[Permission]:
        """获取用户的权限列表"""
        return await permission_repository.get_user_permissions(db, user_id=user_id)


rbac_service = RBACService()
