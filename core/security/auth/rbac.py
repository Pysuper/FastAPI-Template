from datetime import datetime
from typing import Any, Coroutine, Dict, List, Optional, Set

from core.security.core.base import SecurityBase
from core.security.core.exceptions import AuthorizationError


class Role:
    """角色类"""

    def __init__(self, name: str, description: str = "", permissions: Optional[List[str]] = None):
        self.inheritance = None
        self.name = name
        self.description = description
        self.permissions = set(permissions or [])
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def add_permission(self, permission: str) -> None:
        """添加权限"""
        self.permissions.add(permission)
        self.updated_at = datetime.now()

    def remove_permission(self, permission: str) -> None:
        """移除权限"""
        self.permissions.discard(permission)
        self.updated_at = datetime.now()

    def has_permission(self, permission: str) -> bool:
        """检查是否有权限"""
        return permission in self.permissions


class RBACManager(SecurityBase):
    """RBAC管理器"""

    def __init__(self):
        super().__init__()
        self._role_inheritance = {}
        self._role_permissions = {}
        self._roles: Dict[str, Role] = {}
        self._user_roles: Dict[str, Set[str]] = {}

    async def init(self):
        """初始化 RBAC 管理器"""
        try:
            # 初始化角色权限缓存
            self._role_permissions = {}
            # 初始化角色继承关系缓存
            self._role_inheritance = {}
            # 记录初始化状态
            self.logger.info("RBAC manager initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing RBAC manager: {str(e)}")
            raise

    def create_role(self, name: str, description: str = "", permissions: Optional[List[str]] = None) -> Role:
        """创建角色"""
        if name in self._roles:
            raise ValueError(f"角色 {name} 已存在")
        role = Role(name, description, permissions)
        self._roles[name] = role
        return role

    def delete_role(self, name: str) -> None:
        """删除角色"""
        if name not in self._roles:
            raise ValueError(f"角色 {name} 不存在")
        # 从所有用户中移除该角色
        for user_roles in self._user_roles.values():
            user_roles.discard(name)
        del self._roles[name]

    def assign_role_to_user(self, user_id: str, role_name: str) -> None:
        """为用户分配角色"""
        if role_name not in self._roles:
            raise ValueError(f"角色 {role_name} 不存在")
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        self._user_roles[user_id].add(role_name)

    def remove_role_from_user(self, user_id: str, role_name: str) -> None:
        """移除用户的角色"""
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_name)

    def get_user_roles(self, user_id: str) -> List[Role]:
        """获取用户的所有角色"""
        role_names = self._user_roles.get(user_id, set())
        return [self._roles[name] for name in role_names if name in self._roles]

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """获取用户的所有权限"""
        permissions = set()
        for role in self.get_user_roles(user_id):
            permissions.update(role.permissions)
        return permissions

    def check_permission(self, user_id: str, required_permission: str) -> bool:
        """检查用户是否有指定权限"""
        user_permissions = self.get_user_permissions(user_id)
        return required_permission in user_permissions

    def require_permission(self, user_id: str, required_permission: str) -> None:
        """要求用户必须有指定权限"""
        if not self.check_permission(user_id, required_permission):
            raise AuthorizationError(
                message=f"需要权限: {required_permission}",
                details={
                    "user_id": user_id,
                    "required_permission": required_permission,
                    "user_permissions": list(self.get_user_permissions(user_id)),
                },
            )

    def get_role_hierarchy(self) -> Dict[str, List[str]]:
        """获取角色层级结构"""
        hierarchy = {}
        for role_name, role in self._roles.items():
            hierarchy[role_name] = list(role.permissions)
        return hierarchy

    async def close(self):
        """关闭RBAC管理器并清理资源"""
        try:
            # 清理角色权限缓存
            if self._role_permissions is not None:
                self._role_permissions.clear()
            # 清理角色继承关系缓存
            if self._role_inheritance is not None:
                self._role_inheritance.clear()
            # 清理角色和用户角色映射
            self._roles.clear()
            self._user_roles.clear()
            # 记录关闭状态
            self.logger.info("RBAC manager closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing RBAC manager: {str(e)}")
            raise

    async def reload(self, config):
        """重新加载RBAC配置"""
        try:
            # 重新加载 RBAC 管理器
            if self._role_permissions is not None:
                self._role_permissions.clear()
            if self._role_inheritance is not None:
                self._role_inheritance.clear()
            if self._roles is not None:
                self._roles.clear()
            if self._user_roles is not None:
                self._user_roles.clear()

            # 重新读取角色和权限数据
            # ...

            # 记录重新加载状态
            self.logger.info("RBAC manager reloaded successfully")
        except Exception as e:
            self.logger.error(f"Error reloading RBAC manager: {str(e)}")
            raise

    async def update_role(self, name: str, description: str = "", permissions: Optional[List[str]] = None) -> None:
        """更新角色"""
        if name not in self._roles:
            raise ValueError(f"角色 {name} 不存在")
        role = self._roles[name]
        role.description = description
        role.permissions = set(permissions or [])
        role.updated_at = datetime.now()

    async def update_user_roles(self, user_id: str, role_names: List[str]) -> None:
        """更新用户的角色"""
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        user_roles = self._user_roles[user_id]
        for role_name in role_names:
            if role_name not in self._roles:
                raise ValueError(f"角色 {role_name} 不存在")
            user_roles.add(role_name)
        self._user_roles[user_id] = user_roles

    async def update_role_permissions(self, name: str, permissions: List[str]) -> None:
        """更新角色的权限"""
        if name not in self._roles:
            raise ValueError(f"角色 {name} 不存在")
        role = self._roles[name]
        role.permissions = set(permissions)
        role.updated_at = datetime.now()

    async def update_role_inheritance(self, name: str, inheritance: List[str]) -> None:
        """更新角色的继承关系"""
        if name not in self._roles:
            raise ValueError(f"角色 {name} 不存在")
        role = self._roles[name]
        role.inheritance = set(inheritance)
        role.updated_at = datetime.now()

    async def update_role_hierarchy(self, hierarchy: Dict[str, List[str]]) -> None:
        """更新角色层级结构"""
        # 先清理所有角色的继承关系
        for role in self._roles.values():
            role.inheritance = set()
        # 再更新角色的继承关系
        for role_name, inheritance in hierarchy.items():
            if role_name not in self._roles:
                raise ValueError(f"角色 {role_name} 不存在")
            role = self._roles[role_name]
            role.inheritance = set(inheritance)
        # 记录更新状态
        self.logger.info("RBAC role hierarchy updated successfully")

    async def export_role_permissions(self) -> Dict[str, List[str]]:
        """导出角色权限"""
        permissions = {}
        for role_name, role in self._roles.items():
            permissions[role_name] = list(role.permissions)
        return permissions

    async def import_role_permissions(self, permissions: Dict[str, List[str]]) -> None:
        """导入角色权限"""
        for role_name, role_permissions in permissions.items():
            if role_name not in self._roles:
                raise ValueError(f"角色 {role_name} 不存在")
            role = self._roles[role_name]
            role.permissions = set(role_permissions)
        # 记录导入状态
        self.logger.info("RBAC role permissions imported successfully")

    async def export_role_hierarchy(self) -> Dict[str, List[str]]:
        """导出角色层级结构"""
        hierarchy = {}
        for role_name, role in self._roles.items():
            hierarchy[role_name] = list(role.inheritance)
        return hierarchy

    async def import_role_hierarchy(self, hierarchy: Dict[str, List[str]]) -> None:
        """导入角色层级结构"""
        for role_name, role_inheritance in hierarchy.items():
            if role_name not in self._roles:
                raise ValueError(f"角色 {role_name} 不存在")
            role = self._roles[role_name]
            role.inheritance = set(role_inheritance)
        # 记录导入状态
        self.logger.info("RBAC role hierarchy imported successfully")

    async def export_user_roles(self) -> Dict[str, List[str]]:
        """导出用户角色"""
        user_roles = {}
        for user_id, role_names in self._user_roles.items():
            user_roles[user_id] = list(role_names)
        return user_roles

    async def import_user_roles(self, user_roles: Dict[str, List[str]]) -> None:
        """导入用户角色"""
        for user_id, role_names in user_roles.items():
            if user_id not in self._user_roles:
                self._user_roles[user_id] = set()
            user_roles = self._user_roles[user_id]
            for role_name in role_names:
                if role_name not in self._roles:
                    raise ValueError(f"角色 {role_name} 不存在")
                user_roles.add(role_name)
        # 记录导入状态
        self.logger.info("RBAC user roles imported successfully")

    async def export_all(self) -> dict[str, Coroutine[Any, Any, dict[str, list[str]]]]:
        """导出所有 RBAC 配置"""
        return {
            "roles": self.export_role_permissions(),
            "hierarchy": self.export_role_hierarchy(),
            "users": self.export_user_roles(),
        }

    async def import_all(self, data: Dict[str, List]) -> None:
        """导入所有 RBAC 配置"""
        await self.import_role_permissions(data["roles"])
        await self.import_role_hierarchy(data["hierarchy"])
        await self.import_user_roles(data["users"])
        # 记录导入状态
        self.logger.info("RBAC configuration imported successfully")

    async def backup(self) -> None:
        """备份 RBAC 配置"""
        pass

    async def restore(self) -> None:
        pass
