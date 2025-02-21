"""
用户数据访问层
实现用户相关的所有数据库操作
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories import BaseRepository
from schemas.validators.rbac import UserCreate, UserUpdate
from models.user import User
from utils.security import get_password_hash, verify_password


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    用户仓储类
    实现用户特定的数据库操作
    """

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        """
        query = select(User).where(User.email == email, User.is_deleted == False)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        通过用户名获取用户
        """
        query = select(User).where(User.username == username, User.is_deleted == False)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        创建用户
        """
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate) -> User:
        """
        更新用户
        """
        update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        """
        用户认证
        """
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """
        检查用户是否激活
        """
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """
        检查是否是超级用户
        """
        return user.is_superuser


# 创建用户仓储实例
user_repository = UserRepository(User)
