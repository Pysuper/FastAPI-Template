"""
权限缓存管理器
实现权限和角色的缓存机制
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

from fastapi import Request

from core.config.setting import settings


class PermissionCache:
    """权限缓存条目"""

    def __init__(self, permissions: Set[str], roles: Set[str], expires_at: datetime):
        self.permissions = permissions
        self.roles = roles
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "permissions": list(self.permissions),
            "roles": list(self.roles),
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PermissionCache":
        return cls(
            permissions=set(data["permissions"]),
            roles=set(data["roles"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )


class PermissionCacheManager:
    """
    权限缓存管理器
    处理权限和角色的缓存
    """

    def __init__(self):
        self.cache = settings.cache
        self._local_cache: Dict[str, PermissionCache] = {}

    @property
    def config(self):
        from core.config.manager import config_manager

        return config_manager.security

    def _get_cache_key(self, user_id: str) -> str:
        """生成缓存键"""
        return f"permissions:user:{user_id}"

    async def get_permissions(self, user_id: str) -> Optional[PermissionCache]:
        """
        获取用户权限缓存
        :param user_id: 用户ID
        :return: 权限缓存对象
        """
        # 先检查本地缓存
        if user_id in self._local_cache:
            cache = self._local_cache[user_id]
            if not cache.is_expired():
                return cache
            del self._local_cache[user_id]

        # 检查Redis缓存
        cache_key = self._get_cache_key(user_id)
        cached_data = await self.cache.get(cache_key)

        if cached_data:
            try:
                cache = PermissionCache.from_dict(json.loads(cached_data))
                if not cache.is_expired():
                    # 更新本地缓存
                    self._local_cache[user_id] = cache
                    return cache
            except Exception:
                pass

        return None

    async def set_permissions(
        self,
        user_id: str,
        permissions: Set[str],
        roles: Set[str],
        ttl: Optional[int] = None,
    ) -> None:
        """
        设置用户权限缓存
        :param user_id: 用户ID
        :param permissions: 权限集合
        :param roles: 角色集合
        :param ttl: 过期时间(秒)
        """
        if ttl is None:
            ttl = self.config.SESSION_EXPIRE_MINUTES * 60

        expires_at = datetime.now() + timedelta(seconds=ttl)
        cache = PermissionCache(permissions, roles, expires_at)

        # 更新本地缓存
        self._local_cache[user_id] = cache

        # 更新Redis缓存
        cache_key = self._get_cache_key(user_id)
        await self.cache.set(cache_key, json.dumps(cache.to_dict()), ttl)

    async def invalidate_permissions(self, user_id: str) -> None:
        """
        使用户权限缓存失效
        :param user_id: 用户ID
        """
        # 清除本地缓存
        if user_id in self._local_cache:
            del self._local_cache[user_id]

        # 清除Redis缓存
        cache_key = self._get_cache_key(user_id)
        await self.cache.delete(cache_key)

    async def invalidate_all(self) -> None:
        """使所有权限缓存失效"""
        # 清除本地缓存
        self._local_cache.clear()

        # 清除Redis缓存
        pattern = "permissions:user:*"
        await self.cache.delete_pattern(pattern)

    async def get_user_permissions(self, request: Request) -> Set[str]:
        """
        获取请求用户的权限
        :param request: 请求对象
        :return: 权限集合
        """
        user = getattr(request.state, "user", None)
        if not user:
            return set()

        cache = await self.get_permissions(user["id"])
        if cache:
            return cache.permissions

        return set()

    async def init(self):
        pass

    async def close(self):
        pass

    async def reload(self, config):
        pass


# 创建权限缓存管理器实例
permission_cache = PermissionCacheManager()

# 导出权限缓存管理器
__all__ = ["permission_cache"]
