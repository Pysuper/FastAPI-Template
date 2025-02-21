from typing import List, Optional

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api.base.crud import NotFoundError
from models import User
from repositories import user_repository
from schemas.base.pagination import PaginationParams
from schemas.validators.rbac import UserCreate, UserUpdate
from services.rbac import rbac_service


class UserService:
    @staticmethod
    async def create_user(
        db: AsyncSession,
        *,
        user_in: UserCreate,
        role_ids: Optional[List[int]] = None,
    ) -> User:
        """创建用户"""
        # 检查邮箱是否已存在
        if await user_repository.get_by_email(db, email=user_in.email):
            raise ValidationError("邮箱已被注册")

        # 检查用户名是否已存在
        if await user_repository.get_by_username(db, username=user_in.username):
            raise ValidationError("用户名已被使用")

        # 创建用户
        user = await user_repository.create(db, obj_in=user_in)

        # 分配角色
        if role_ids:
            for role_id in role_ids:
                await rbac_service.assign_role_to_user(db, user_id=user.id, role_id=role_id)

        return user

    @staticmethod
    async def update_user(
        db: AsyncSession,
        *,
        user_id: int,
        user_in: UserUpdate,
        role_ids: Optional[List[int]] = None,
    ) -> User:
        """更新用户"""
        # 获取用户
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise NotFoundError("用户不存在")

        # 检查邮箱是否已存在
        if user_in.email and user_in.email != user.email:
            if await user_repository.get_by_email(db, email=user_in.email):
                raise ValidationError("邮箱已被使用")

        # 检查用户名是否已存在
        if user_in.username and user_in.username != user.username:
            if await user_repository.get_by_username(db, username=user_in.username):
                raise ValidationError("用户名已被使用")

        # 更新用户
        user = await user_repository.update(db, db_obj=user, obj_in=user_in)

        # 更新角色
        if role_ids is not None:
            # 获取当前角色
            current_roles = await rbac_service.get_user_roles(db, user_id=user.id)
            current_role_ids = {r.id for r in current_roles}

            # 需要添加的角色
            to_add = set(role_ids) - current_role_ids
            for role_id in to_add:
                await rbac_service.assign_role_to_user(db, user_id=user.id, role_id=role_id)

            # 需要移除的角色
            to_remove = current_role_ids - set(role_ids)
            for role_id in to_remove:
                await rbac_service.remove_role_from_user(db, user_id=user.id, role_id=role_id)

        return user

    @staticmethod
    async def delete_user(db: AsyncSession, *, user_id: int) -> User:
        """删除用户"""
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise NotFoundError("用户不存在")
        return await user_repository.remove(db, id=user_id)

    @staticmethod
    async def get_users(
        db: AsyncSession,
        *,
        pagination: PaginationParams,
        email: Optional[str] = None,
        username: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
    ) -> tuple[List[User], int]:
        """获取用户列表"""
        filters = {}
        if email:
            filters["email"] = email
        if username:
            filters["username"] = username
        if is_active is not None:
            filters["is_active"] = is_active
        if is_superuser is not None:
            filters["is_superuser"] = is_superuser
        return await user_repository.get_multi(db, pagination=pagination, **filters)

    @staticmethod
    async def activate_user(db: AsyncSession, *, user_id: int) -> User:
        """激活用户"""
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise NotFoundError("用户不存在")

        if user.is_active:
            return user

        user_in = {"is_active": True}
        return await user_repository.update(db, db_obj=user, obj_in=user_in)

    @staticmethod
    async def deactivate_user(db: AsyncSession, *, user_id: int) -> User:
        """禁用用户"""
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise NotFoundError("用户不存在")

        if not user.is_active:
            return user

        if user.is_superuser:
            raise ValidationError("不能禁用超级用户")

        user_in = {"is_active": False}
        return await user_repository.update(db, db_obj=user, obj_in=user_in)

    @staticmethod
    async def set_superuser(db: AsyncSession, *, user_id: int, is_superuser: bool) -> User:
        """设置超级用户状态"""
        user = await user_repository.get(db, id=user_id)
        if not user:
            raise NotFoundError("用户不存在")

        if user.is_superuser == is_superuser:
            return user

        user_in = {"is_superuser": is_superuser}
        return await user_repository.update(db, db_obj=user, obj_in=user_in)


user_service = UserService()
