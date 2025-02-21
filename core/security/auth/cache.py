import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set


class CacheEntry:
    """缓存条目"""

    def __init__(self, value: Any, ttl: int = 300):
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl)
        self.last_accessed = self.created_at
        self.access_count = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.expires_at

    def access(self) -> None:
        """访问缓存"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class PermissionCache:
    """权限缓存"""

    def __init__(self, default_ttl: int = 300, cleanup_interval: int = 60):
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._lock = threading.Lock()

        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl or self._default_ttl)

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return None

            entry.access()
            return entry.value

    def delete(self, key: str) -> None:
        """删除缓存"""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def _cleanup_loop(self) -> None:
        """清理循环"""
        while True:
            time.sleep(self._cleanup_interval)
            self._cleanup_expired()

    def _cleanup_expired(self) -> None:
        """清理过期缓存"""
        with self._lock:
            current_time = datetime.now()
            expired_keys = [key for key, entry in self._cache.items() if current_time > entry.expires_at]
            for key in expired_keys:
                del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
            total_access = sum(entry.access_count for entry in self._cache.values())

            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_entries,
                "expired_entries": expired_entries,
                "total_access": total_access,
                "cache_size": len(self._cache),
                "cleanup_interval": self._cleanup_interval,
                "default_ttl": self._default_ttl,
            }


class UserPermissionCache:
    """用户权限缓存"""

    def __init__(self, ttl: int = 300):
        self._cache = PermissionCache(default_ttl=ttl)

    def get_user_permissions(self, user_id: str) -> Optional[Set[str]]:
        """获取用户权限"""
        return self._cache.get(f"user_permissions:{user_id}")

    def set_user_permissions(self, user_id: str, permissions: Set[str]) -> None:
        """设置用户权限"""
        self._cache.set(f"user_permissions:{user_id}", permissions)

    def get_user_roles(self, user_id: str) -> Optional[Set[str]]:
        """获取用户角色"""
        return self._cache.get(f"user_roles:{user_id}")

    def set_user_roles(self, user_id: str, roles: Set[str]) -> None:
        """设置用户角色"""
        self._cache.set(f"user_roles:{user_id}", roles)

    def invalidate_user(self, user_id: str) -> None:
        """使用户缓存失效"""
        self._cache.delete(f"user_permissions:{user_id}")
        self._cache.delete(f"user_roles:{user_id}")

    def get_role_permissions(self, role_name: str) -> Optional[Set[str]]:
        """获取角色权限"""
        return self._cache.get(f"role_permissions:{role_name}")

    def set_role_permissions(self, role_name: str, permissions: Set[str]) -> None:
        """设置角色权限"""
        self._cache.set(f"role_permissions:{role_name}", permissions)

    def invalidate_role(self, role_name: str) -> None:
        """使角色缓存失效"""
        self._cache.delete(f"role_permissions:{role_name}")

    def clear_all(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
