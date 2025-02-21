from datetime import datetime
from typing import Optional, Tuple

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories import role_repository, user_repository
from core.schemas.validators.rbac import Token, User, UserCreate, UserUpdate
from core.security.core.exceptions import AuthenticationError
from utils.security import create_access_token, verify_password


class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, *, email: str, password: str) -> Tuple[User, Token]:
        """用户认证"""
        # 获取用户
        user = await user_repository.get_by_email(db, email=email)
        if not user:
            raise AuthenticationError("邮箱或密码错误")

        # 验证密码
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("邮箱或密码错误")

        # 检查用户状态
        if not user.is_active:
            raise AuthenticationError("用户已被禁用")

        # 更新最后登录时间
        user.last_login = datetime.now()
        await db.commit()

        # 生成访问令牌
        access_token = create_access_token(subject=user.email)
        return user, Token(access_token=access_token, token_type="bearer")

    @staticmethod
    async def register(db: AsyncSession, *, user_in: UserCreate, auto_activate: bool = True) -> User:
        """用户注册"""
        # 检查邮箱是否已存在
        if await user_repository.get_by_email(db, email=user_in.email):
            raise ValidationError("邮箱已被注册")

        # 检查用户名是否已存在
        if await user_repository.get_by_username(db, username=user_in.username):
            raise ValidationError("用户名已被使用")

        # 创建用户
        user = await user_repository.create(db, obj_in=user_in)

        # 分配默认角色
        default_role = await role_repository.get_by_name(db, name="user")
        if default_role:
            await role_repository.add_user(db, role_id=default_role.id, user_id=user.id)

        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        *,
        user: User,
        current_password: str,
        new_password: str,
    ) -> User:
        """修改密码"""
        # 验证当前密码
        if not verify_password(current_password, user.hashed_password):
            raise ValidationError("当前密码错误")

        # 更新密码
        user_in = UserUpdate(password=new_password)
        return await user_repository.update(db, db_obj=user, obj_in=user_in)

    @staticmethod
    async def reset_password(db: AsyncSession, *, email: str, new_password: str) -> Optional[User]:
        """重置密码"""
        user = await user_repository.get_by_email(db, email=email)
        if not user:
            return None

        user_in = UserUpdate(password=new_password)
        return await user_repository.update(db, db_obj=user, obj_in=user_in)

    @staticmethod
    async def update_profile(db: AsyncSession, *, user: User, user_in: UserUpdate) -> User:
        """更新用户资料"""
        # 如果要更新邮箱，检查是否已存在
        if user_in.email and user_in.email != user.email:
            if await user_repository.get_by_email(db, email=user_in.email):
                raise ValidationError("邮箱已被使用")

        # 如果要更新用户名，检查是否已存在
        if user_in.username and user_in.username != user.username:
            if await user_repository.get_by_username(db, username=user_in.username):
                raise ValidationError("用户名已被使用")

        return await user_repository.update(db, db_obj=user, obj_in=user_in)


auth_service = AuthService()
