"""
RBAC权限控制系统
实现细粒度的权限控制和继承机制
"""

from enum import Enum
from functools import wraps
from typing import Dict, List, Optional, Set, Union

from fastapi import HTTPException, Request

from core.middlewares.api_audit import audit_manager
from security.auth.permission_cache import permission_cache


class PermissionType(str, Enum):
    """权限类型"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """资源类型"""

    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SYSTEM = "system"
    CUSTOM = "custom"


class Permission:
    """权限对象"""

    def __init__(
        self,
        resource_type: Union[ResourceType, str],
        permission_type: Union[PermissionType, str],
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.resource_type = resource_type
        self.permission_type = permission_type
        self.resource_id = resource_id
        self.description = description

    def to_string(self) -> str:
        """转换为字符串格式"""
        if self.resource_id:
            return f"{self.resource_type}:{self.permission_type}:{self.resource_id}"
        return f"{self.resource_type}:{self.permission_type}"

    @classmethod
    def from_string(cls, permission_str: str) -> "Permission":
        """从字符串解析权限对象"""
        parts = permission_str.split(":")
        if len(parts) == 3:
            return cls(parts[0], parts[1], parts[2])
        return cls(parts[0], parts[1])


class RBACManager:
    """
    RBAC权限管理器
    实现权限检查和继承机制
    """

    def __init__(self):
        self._role_permissions: Dict[str, Set[str]] = {}
        self._role_inheritance: Dict[str, Set[str]] = {}

    def add_role_permissions(self, role: str, permissions: List[Union[Permission, str]]) -> None:
        """
        添加角色权限
        :param role: 角色名称
        :param permissions: 权限列表
        """
        if role not in self._role_permissions:
            self._role_permissions[role] = set()

        for permission in permissions:
            if isinstance(permission, Permission):
                self._role_permissions[role].add(permission.to_string())
            else:
                self._role_permissions[role].add(permission)

    def add_role_inheritance(self, role: str, inherit_from: str) -> None:
        """
        添加角色继承关系
        :param role: 角色名称
        :param inherit_from: 继承自哪个角色
        """
        if role not in self._role_inheritance:
            self._role_inheritance[role] = set()
        self._role_inheritance[role].add(inherit_from)

    def get_role_permissions(self, role: str) -> Set[str]:
        """
        获取角色的所有权限(包括继承的权限)
        :param role: 角色名称
        :return: 权限集合
        """
        permissions = set()

        # 添加直接权限
        if role in self._role_permissions:
            permissions.update(self._role_permissions[role])

        # 添加继承的权限
        if role in self._role_inheritance:
            for inherited_role in self._role_inheritance[role]:
                permissions.update(self.get_role_permissions(inherited_role))

        return permissions

    def has_permission(self, required_permission: Union[Permission, str], user_permissions: Set[str]) -> bool:
        """
        检查是否有权限
        :param required_permission: 所需权限
        :param user_permissions: 用户权限集合
        :return: 是否有权限
        """
        if isinstance(required_permission, Permission):
            permission_str = required_permission.to_string()
        else:
            permission_str = required_permission

        # 检查完整权限匹配
        if permission_str in user_permissions:
            return True

        # 检查通配符权限
        permission = Permission.from_string(permission_str)
        wildcard_permissions = [
            f"{permission.resource_type}:*",
            f"{permission.resource_type}:{permission.permission_type}:*",
            "*:*",
            f"*:{permission.permission_type}",
        ]

        return any(p in user_permissions for p in wildcard_permissions)

    async def init(self):
        pass

    async def close(self):
        pass

    async def reload(self, config):
        pass


class RBACMiddleware:
    """RBAC中间件"""

    def __init__(self, rbac: RBACManager):
        self.rbac = rbac

    async def __call__(self, request: Request, call_next):
        # 获取用户权限
        user_permissions = await permission_cache.get_user_permissions(request)

        # 将权限集合添加到请求状态
        request.state.permissions = user_permissions

        # 记录审计日志
        await audit_manager.log_request(request)

        response = await call_next(request)

        # 记录响��审计日志
        await audit_manager.log_request(request, response)

        return response


def requires_permission(permission: Union[Permission, str]):
    """
    权限检查装饰器
    :param permission: 所需权限
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            user_permissions = getattr(request.state, "permissions", set())

            if not rbac_manager.has_permission(permission, user_permissions):
                raise HTTPException(status_code=403, detail="Permission denied")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 创建RBAC管理器实例
rbac_manager = RBACManager()
# 导出RBAC组件
__all__ = ["rbac_manager", "RBACMiddleware", "requires_permission", "Permission", "PermissionType", "ResourceType"]
