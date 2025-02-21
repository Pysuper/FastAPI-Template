# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：permission.py
@Author  ：PySuper
@Date    ：2025/1/3 13:26 
@Desc    ：权限服务模块

提供权限管理的核心服务功能
支持权限的CRUD操作和高级查询
"""
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.cache.manager import cache_manager
from exceptions.business.auth import AuthBusinessException
from exceptions.http.validation import ValidationException
from models.permission import Permission
from models.role import Role


class PermissionService:
    """权限服务类

    提供权限管理相关的服务方法
    包括权限的增删改查和高级操作
    """

    def __init__(self, permission_repo):
        """初始化权限服务

        Args:
            permission_repo: 权限仓储对象
        """
        self.permission_repo = permission_repo
        self.cache = cache_manager

    async def get_all_permissions(
        self, db: Session, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[Permission]:
        """获取所有权限

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            filters: 过滤条件

        Returns:
            权限列表

        Raises:
            HTTPException: 查询失败时抛出
        """
        try:
            cache_key = f"permissions:all:{skip}:{limit}:{filters}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            permissions = await self.permission_repo.get_all_permissions(db, skip=skip, limit=limit, filters=filters)

            await self.cache.set(cache_key, permissions, ttl=300)  # 缓存5分钟
            return permissions

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取权限列表失败: {str(e)}")

    async def get_permission_by_id(self, db: Session, permission_id: int) -> Optional[Permission]:
        """根据ID获取权限

        Args:
            db: 数据库会话
            permission_id: 权限ID

        Returns:
            权限对象,不存在时返回None

        Raises:
            HTTPException: 查询失败时抛出
        """
        try:
            cache_key = f"permissions:id:{permission_id}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            permission = await self.permission_repo.get_permission_by_id(db, permission_id)
            if not permission:
                return None

            await self.cache.set(cache_key, permission, ttl=300)
            return permission

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取权限失败: {str(e)}")

    async def get_permission_by_code(self, db: Session, code: str) -> Optional[Permission]:
        """根据权限代码获取权限

        Args:
            db: 数据库会话
            code: 权限代码

        Returns:
            权限对象,不存在时返回None

        Raises:
            HTTPException: 查询失败时抛出
        """
        try:
            cache_key = f"permissions:code:{code}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            permission = await self.permission_repo.get_permission_by_code(db, code)
            if not permission:
                return None

            await self.cache.set(cache_key, permission, ttl=300)
            return permission

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取权限失败: {str(e)}")

    async def create_permission(
        self, db: Session, code: str, name: str, description: Optional[str] = None
    ) -> Permission:
        """创建权限

        Args:
            db: 数据库会话
            code: 权限代码
            name: 权限名称
            description: 权限描述

        Returns:
            创建的权限对象

        Raises:
            ValidationException: 参数验证失败时抛出
            HTTPException: 创建失败时抛出
        """
        try:
            # 验证权限代码是否已存在
            existing = await self.get_permission_by_code(db, code)
            if existing:
                raise ValidationException(f"权限代码 {code} 已存在")

            permission = await self.permission_repo.create_permission(db, code=code, name=name, description=description)

            # 清除相关缓存
            await self.cache.delete_pattern("permissions:*")

            return permission

        except ValidationException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建权限失败: {str(e)}")

    async def update_permission(
        self,
        db: Session,
        permission_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Permission:
        """更新权限

        Args:
            db: 数据库会话
            permission_id: 权限ID
            name: 权限名称
            description: 权限描述
            is_active: 是否激活

        Returns:
            更新后的权限对象

        Raises:
            AuthBusinessException: 权限不存在时抛出
            HTTPException: 更新失败时抛出
        """
        try:
            permission = await self.get_permission_by_id(db, permission_id)
            if not permission:
                raise AuthBusinessException(f"权限ID {permission_id} 不存在")

            permission = await self.permission_repo.update_permission(
                db, permission_id=permission_id, name=name, description=description, is_active=is_active
            )

            # 清除相关缓存
            await self.cache.delete_pattern("permissions:*")

            return permission

        except AuthBusinessException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新权限失败: {str(e)}")

    async def delete_permission(self, db: Session, permission_id: int) -> bool:
        """删除权限

        Args:
            db: 数据库会话
            permission_id: 权限ID

        Returns:
            是否删除成功

        Raises:
            AuthBusinessException: 权限不存在时抛出
            HTTPException: 删除失败时抛出
        """
        try:
            permission = await self.get_permission_by_id(db, permission_id)
            if not permission:
                raise AuthBusinessException(f"权限ID {permission_id} 不存在")

            result = await self.permission_repo.delete_permission(db, permission_id)

            # 清除相关缓存
            await self.cache.delete_pattern("permissions:*")

            return result

        except AuthBusinessException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除权限失败: {str(e)}")

    async def get_user_permissions(self, db: Session, user_id: int) -> List[Permission]:
        """获取用户的所有权限

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            权限列表

        Raises:
            HTTPException: 查询失败时抛出
        """
        try:
            cache_key = f"permissions:user:{user_id}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            permissions = await self.permission_repo.get_user_permissions(db, user_id)

            await self.cache.set(cache_key, permissions, ttl=300)
            return permissions

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取用户权限失败: {str(e)}")

    async def get_role_permissions(self, db: Session, role_id: int) -> List[Permission]:
        """获取角色的所有权限

        Args:
            db: 数据库会话
            role_id: 角色ID

        Returns:
            权限列表

        Raises:
            HTTPException: 查询失败时抛出
        """
        try:
            cache_key = f"permissions:role:{role_id}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return cached_result

            permissions = await self.permission_repo.get_role_permissions(db, role_id)

            await self.cache.set(cache_key, permissions, ttl=300)
            return permissions

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取角色权限失败: {str(e)}")

    async def assign_permissions_to_role(self, db: Session, role_id: int, permission_ids: List[int]) -> bool:
        """为角色分配权限

        Args:
            db: 数据库会话
            role_id: 角色ID
            permission_ids: 权限ID列表

        Returns:
            是否分配成功

        Raises:
            AuthBusinessException: 角色或权限不存在时抛出
            HTTPException: 分配失败时抛出
        """
        try:
            # 验证角色是否存在
            role = await self.permission_repo.get_role_by_id(db, role_id)
            if not role:
                raise AuthBusinessException(f"角色ID {role_id} 不存在")

            # 验证权限是否都存在
            for permission_id in permission_ids:
                permission = await self.get_permission_by_id(db, permission_id)
                if not permission:
                    raise AuthBusinessException(f"权限ID {permission_id} 不存在")

            result = await self.permission_repo.assign_permissions_to_role(
                db, role_id=role_id, permission_ids=permission_ids
            )

            # 清除相关缓存
            await self.cache.delete_pattern(f"permissions:role:{role_id}")
            await self.cache.delete_pattern("permissions:user:*")

            return result

        except AuthBusinessException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"分配权限失败: {str(e)}")

    async def revoke_permissions_from_role(self, db: Session, role_id: int, permission_ids: List[int]) -> bool:
        """从角色撤销权限

        Args:
            db: 数据库会话
            role_id: 角色ID
            permission_ids: 权限ID列表

        Returns:
            是否撤销成功

        Raises:
            AuthBusinessException: 角色不存在时抛出
            HTTPException: 撤销失败时抛出
        """
        try:
            # 验证角色是否存在
            role = await self.permission_repo.get_role_by_id(db, role_id)
            if not role:
                raise AuthBusinessException(f"角色ID {role_id} 不存在")

            result = await self.permission_repo.revoke_permissions_from_role(
                db, role_id=role_id, permission_ids=permission_ids
            )

            # 清除相关缓存
            await self.cache.delete_pattern(f"permissions:role:{role_id}")
            await self.cache.delete_pattern("permissions:user:*")

            return result

        except AuthBusinessException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"撤销权限失败: {str(e)}")

    async def check_permission(self, db: Session, user_id: int, permission_code: str) -> bool:
        """检查用户是否拥有指定权限

        Args:
            db: 数据库会话
            user_id: 用户ID
            permission_code: 权限代码

        Returns:
            是否拥有权限
        """
        try:
            user_permissions = await self.get_user_permissions(db, user_id)
            user_permission_codes = {p.code for p in user_permissions}

            # 检查是否有超级管理员权限
            if "super_admin" in user_permission_codes:
                return True

            return permission_code in user_permission_codes

        except Exception:
            return False

    def get_user_permissions_sync(self, db: Session, user_id: int) -> List[Permission]:
        """同步方式获取用户权限(用于装饰器)

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            权限列表
        """
        try:
            return self.permission_repo.get_user_permissions_sync(db, user_id)
        except Exception:
            return []

    def get_user_roles_sync(self, db: Session, user_id: int) -> List[Role]:
        """同步方式获取用户角色(用于装饰器)

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            角色列表
        """
        try:
            return self.permission_repo.get_user_roles_sync(db, user_id)
        except Exception:
            return []
