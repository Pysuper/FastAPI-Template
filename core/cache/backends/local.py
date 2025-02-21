import fnmatch
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional, Union

from core.cache.base.base import BaseCache
from core.cache.manager import cache_manager
from core.config import CacheConfig


class CacheItem:
    """缓存项"""

    def __init__(self, value: Any, expire_at: Optional[datetime] = None):
        self.value = value
        self.expire_at = expire_at
        self.created_at = datetime.now()
        self.accessed_at = self.created_at
        self.access_count = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expire_at is None:
            return False
        return datetime.now() > self.expire_at

    def access(self):
        """更新访问信息"""
        self.accessed_at = datetime.now()
        self.access_count += 1


class LocalCache(BaseCache):
    """
    本地缓存实现
    提供进程内存缓存功能
    """

    def __init__(self, config: CacheConfig):
        super().__init__(config)
        self.config = cache_manager.config
        self._cache: Dict[str, CacheItem] = {}
        self._lock = Lock()
        self._lock_waiters: Dict[str, List[str]] = {}
        self._lock_owners: Dict[str, str] = {}

    async def init(self):
        """初始化缓存"""
        pass

    async def close(self):
        """关闭缓存"""
        await self.clear()

    def _cleanup(self):
        """清理过期缓存"""
        with self._lock:
            now = datetime.now()
            expired_keys = [key for key, item in self._cache.items() if item.is_expired()]
            for key in expired_keys:
                del self._cache[key]

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        self._cleanup()
        with self._lock:
            item = self._cache.get(key)
            if item and not item.is_expired():
                item.access()
                return item.value
        return None

    async def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """设置缓存值"""
        self._cleanup()
        expire_at = None
        if expire:
            if isinstance(expire, int):
                expire = timedelta(seconds=expire)
            expire_at = datetime.now() + expire
        with self._lock:
            self._cache[key] = CacheItem(value, expire_at)
        return True

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
        return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        self._cleanup()
        with self._lock:
            item = self._cache.get(key)
            return item is not None and not item.is_expired()

    async def clear(self) -> bool:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._lock_waiters.clear()
            self._lock_owners.clear()
        return True

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取多个缓存值"""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(self, mapping: Dict[str, Any], expire: Optional[Union[int, timedelta]] = None) -> bool:
        """批量设置多个缓存值"""
        for key, value in mapping.items():
            await self.set(key, value, expire)
        return True

    async def delete_many(self, keys: List[str]) -> bool:
        """批量删除多个缓存值"""
        for key in keys:
            await self.delete(key)
        return True

    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存键"""
        count = 0
        with self._lock:
            keys = list(self._cache.keys())
            for key in keys:
                if fnmatch.fnmatch(key, pattern):
                    if await self.delete(key):
                        count += 1
        return count

    async def get_or_set(
        self, key: str, value_generator: callable, expire: Optional[Union[int, timedelta]] = None
    ) -> Any:
        """获取缓存值，如果不存在则设置"""
        value = await self.get(key)
        if value is not None:
            return value
        value = value_generator()
        if value is not None:
            await self.set(key, value, expire)
        return value

    async def get_ttl(self, key: str) -> int:
        """获取缓存值的剩余有效时间"""
        with self._lock:
            item = self._cache.get(key)
            if item and item.expire_at:
                ttl = (item.expire_at - datetime.now()).total_seconds()
                return max(0, int(ttl))
        return -2

    async def persist(self, key: str) -> bool:
        """使缓存值持久化"""
        with self._lock:
            item = self._cache.get(key)
            if item:
                item.expire_at = None
                return True
        return False

    async def lock(self, key: str, timeout: Optional[int] = None) -> bool:
        """加锁"""
        lock_key = f"lock:{key}"
        if await self.exists(lock_key):
            return False
        await self.set(lock_key, True, timeout or self.config.lock_timeout)
        return True

    async def unlock(self, key: str) -> bool:
        """解锁"""
        lock_key = f"lock:{key}"
        return await self.delete(lock_key)

    async def get_lock(self, key: str) -> bool:
        """获取锁状态"""
        lock_key = f"lock:{key}"
        return await self.exists(lock_key)

    async def release_lock(self, key: str) -> bool:
        """释放锁"""
        return await self.unlock(key)

    async def get_lock_info(self, key: str) -> dict:
        """获取锁信息"""
        lock_key = f"lock:{key}"
        exists = await self.exists(lock_key)
        ttl = await self.get_ttl(lock_key) if exists else -2
        return {
            "exists": exists,
            "ttl": ttl,
            "owner": await self.get_lock_owner(key),
            "waiters": await self.get_lock_waiters(key),
        }

    async def get_lock_status(self, key: str) -> bool:
        """获取锁状态"""
        return await self.get_lock(key)

    async def get_lock_owner(self, key: str) -> Optional[str]:
        """获取锁持有者"""
        with self._lock:
            return self._lock_owners.get(key)

    async def get_lock_waiters(self, key: str) -> List[str]:
        """获取锁等待者列表"""
        with self._lock:
            return self._lock_waiters.get(key, [])

    async def get_lock_waiter_info(self, key: str) -> dict:
        """获取锁等待者信息"""
        return {
            "exists": await self.get_lock(key),
            "ttl": await self.get_ttl(f"lock:{key}"),
            "owner": await self.get_lock_owner(key),
            "waiters": await self.get_lock_waiters(key),
        }

    async def get_lock_waiter_status(self, key: str) -> bool:
        """获取锁等待者状态"""
        waiters = await self.get_lock_waiters(key)
        return bool(waiters)

    async def get_lock_waiter_owner(self, key: str) -> Optional[str]:
        """获取锁等待者持有者"""
        waiters = await self.get_lock_waiters(key)
        return waiters[0] if waiters else None

    async def get_lock_waiter_count(self, key: str) -> int:
        """获取锁等待者数量"""
        waiters = await self.get_lock_waiters(key)
        return len(waiters)

    async def get_lock_waiter_wait_time(self, key: str) -> float:
        """获取锁等待者等待时间"""
        return 0.0  # 本地缓存不跟踪等待时间

    async def get_lock_waiter_timeout(self, key: str) -> float:
        """获取锁等待者超时时间"""
        return float(self.config.lock_timeout)

    async def get_lock_waiter_remaining_time(self, key: str) -> float:
        """获取锁等待者剩余时间"""
        ttl = await self.get_ttl(f"lock:{key}")
        return float(max(0, ttl))

    async def get_lock_waiter_last_time(self, key: str) -> float:
        """获取锁等待者最后一次时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_success_time(self, key: str) -> float:
        """获取锁等待者最后一次成功时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_failure_time(self, key: str) -> float:
        """获取锁等待者最后一次失败时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_time(self, key: str) -> float:
        """获取锁等待者最后一次获取锁时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_success_time(self, key: str) -> float:
        """获取锁等待者最后一次获取锁成功时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_failure_time(self, key: str) -> float:
        """获取锁等待者最后一次获取锁失败时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_owner(self, key: str) -> Optional[str]:
        """获取锁等待者最后一次获取锁的持有者"""
        return None  # 本地缓存不跟踪历史信息

    async def get_lock_waiter_last_lock_count(self, key: str) -> int:
        """获取锁等待者最后一次获取锁的次数"""
        return 0  # 本地缓存不跟踪历史信息

    async def get_lock_waiter_last_lock_remaining_time(self, key: str) -> float:
        """获取锁等待者最后一次获取锁的剩余时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_timeout(self, key: str) -> float:
        """获取锁等待者最后一次获取锁的超时时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_wait_time(self, key: str) -> float:
        """获取锁等待者最后一次获取锁的等待时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_owner_remaining_time(self, key: str) -> float:
        """获取锁等待者最后一次获取锁的持有者剩余时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_owner_timeout(self, key: str) -> float:
        """获取锁等待者最后一次获取锁的持有者超时时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_owner_wait_time(self, key: str) -> float:
        """获取锁等待者最后一次获取锁的持有者等待时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def get_lock_waiter_last_lock_owner_remaining_lock_count(self, key: str) -> int:
        """获取锁等待者最后一次获取锁的持有者剩余获取锁次数"""
        return 0  # 本地缓存不跟踪历史信息

    async def get_lock_waiter_last_lock_owner_remaining_lock_wait_time(self, key: str) -> float:
        """获取锁等待者最后一次获取锁的持有者剩余获取锁等待时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def expire(self, key: str, seconds: int) -> bool:
        """设置缓存值的过期时间"""
        with self._lock:
            item = self._cache.get(key)
            if item:
                item.expire_at = datetime.now() + timedelta(seconds=seconds)
                return True
        return False

    async def get_lock_waiter_last_unlock_time(self, key: str) -> float:
        """获取锁等待者最后一次释放锁的时间"""
        return 0.0  # 本地缓存不跟踪历史时间

    async def incr(self, key: str, amount: int = 1) -> int:
        """递增"""
        with self._lock:
            value = await self.get(key)
            if value is None:
                value = 0
            try:
                new_value = int(value) + amount
                await self.set(key, new_value)
                return new_value
            except (TypeError, ValueError):
                raise ValueError(f"Value for key '{key}' is not an integer")

    async def decr(self, key: str, amount: int = 1) -> int:
        """递减"""
        return await self.incr(key, -amount)

    async def get_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        with self._lock:
            total_items = len(self._cache)
            expired_items = sum(1 for item in self._cache.values() if item.is_expired())
            return {
                "total_items": total_items,
                "active_items": total_items - expired_items,
                "expired_items": expired_items,
                "lock_count": len(self._lock_owners),
                "waiter_count": sum(len(waiters) for waiters in self._lock_waiters.values()),
            }

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间（秒）"""
        with self._lock:
            item = self._cache.get(key)
            if not item:
                return -2  # 键不存在
            if item.expire_at is None:
                return -1  # 永不过期
            ttl = (item.expire_at - datetime.now()).total_seconds()
            return max(0, int(ttl))


local_backend = LocalCache()
