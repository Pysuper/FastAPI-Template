"""
增强的本地缓存后端实现

Features:
    1. 线程安全
    2. TTL支持
    3. 访问追踪
    4. 内存优化
    5. 缓存统计
    6. 模式匹配
    7. 批量操作
    8. 锁管理
    9. 事件通知
    10. 缓存预热
"""

import asyncio
import fnmatch
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union, Callable

from core.cache.base.base import BaseCache
from core.cache.base.manager_protocol import CacheManagerProtocol
from core.cache.config.config import CacheConfig

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """缓存统计信息"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_items: int = 0
    total_size: int = 0
    lock_acquisitions: int = 0
    lock_releases: int = 0
    lock_timeouts: int = 0


@dataclass
class CacheItem:
    """
    缓存项

    Attributes:
        value: 缓存的值
        expire_at: 过期时间
        created_at: 创建时间
        accessed_at: 最后访问时间
        access_count: 访问次数
        size: 数据大小(字节)
        version: 数据版本号
        tags: 标签集合
    """

    value: Any
    expire_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    size: int = 0
    version: int = 1
    tags: Set[str] = field(default_factory=set)

    def is_expired(self) -> bool:
        """检查是否过期"""
        return self.expire_at is not None and datetime.now() > self.expire_at

    def access(self) -> None:
        """更新访问信息"""
        self.accessed_at = datetime.now()
        self.access_count += 1

    def update_version(self) -> None:
        """更新版本号"""
        self.version += 1


class LocalLock:
    """本地锁实现"""

    def __init__(self, name: str, timeout: Optional[int] = None, retry_interval: float = 0.1):
        self.name = name
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.lock = asyncio.Lock()
        self.owner: Optional[str] = None
        self.expire_at: Optional[datetime] = None
        self.waiters: List[str] = []

    async def acquire(self, owner: str) -> bool:
        """
        获取锁

        Args:
            owner: 锁持有者标识

        Returns:
            是否获取成功
        """
        if self.timeout:
            try:
                async with asyncio.timeout(self.timeout):
                    while True:
                        if await self._try_acquire(owner):
                            return True
                        await asyncio.sleep(self.retry_interval)
            except asyncio.TimeoutError:
                return False
        else:
            return await self._try_acquire(owner)

    async def _try_acquire(self, owner: str) -> bool:
        """尝试获取锁"""
        if not self.owner or (self.expire_at and datetime.now() > self.expire_at):
            if await self.lock.acquire():
                self.owner = owner
                if self.timeout:
                    self.expire_at = datetime.now() + timedelta(seconds=self.timeout)
                return True
        return False

    async def release(self, owner: str) -> bool:
        """
        释放锁

        Args:
            owner: 锁持有者标识

        Returns:
            是否释放成功
        """
        if self.owner == owner:
            self.owner = None
            self.expire_at = None
            self.lock.release()
            return True
        return False


class LocalCacheBackend(BaseCache):
    """
    增强的本地缓存后端实现

    Features:
        1. 线程安全
        2. TTL支持
        3. 访问追踪
        4. 内存优化
        5. 缓存统计
        6. 模式匹配
        7. 批量操作
        8. 锁管理
        9. 事件通知
        10. 缓存预热
    """

    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        manager: Optional[CacheManagerProtocol] = None,
        max_size: int = 10000,
        cleanup_interval: int = 60,
    ):
        """
        初始化本地缓存后端

        Args:
            config: 缓存配置
            manager: 缓存管理器
            max_size: 最大缓存项数量
            cleanup_interval: 清理间隔(秒)
        """
        super().__init__(config or CacheConfig())
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval

        self._cache: Dict[str, CacheItem] = {}
        self._locks: Dict[str, LocalLock] = {}
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._event_handlers: Dict[str, List[Callable]] = {
            "on_set": [],
            "on_delete": [],
            "on_expire": [],
            "on_evict": [],
        }

    async def init(self) -> None:
        """初始化缓存系统"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Local cache initialized")

    async def close(self) -> None:
        """关闭缓存系统"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self.clear()
        logger.info("Local cache closed")

    async def _cleanup_loop(self) -> None:
        """清理循环任务"""
        while True:
            try:
                await self._cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Cache cleanup failed: {e}")

    async def _cleanup(self) -> None:
        """清理过期和超量的缓存项"""
        async with self._lock:
            # 清理过期项
            now = datetime.now()
            expired_keys = [key for key, item in self._cache.items() if item.is_expired()]
            for key in expired_keys:
                await self._delete_item(key, "expire")

            # 清理超量项
            if len(self._cache) > self.max_size:
                items = sorted(self._cache.items(), key=lambda x: (x[1].accessed_at, -x[1].access_count))
                remove_count = len(items) - self.max_size
                for key, _ in items[:remove_count]:
                    await self._delete_item(key, "evict")

    async def _delete_item(self, key: str, reason: str) -> None:
        """
        删除缓存项

        Args:
            key: 缓存键
            reason: 删除原因
        """
        if item := self._cache.pop(key, None):
            self._stats.total_items -= 1
            self._stats.total_size -= item.size
            if reason == "evict":
                self._stats.evictions += 1
            await self._notify_event(f"on_{reason}", key, item)

    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        async with self._lock:
            if item := self._cache.get(key):
                if item.is_expired():
                    await self._delete_item(key, "expire")
                    self._stats.misses += 1
                    return default
                item.access()
                self._stats.hits += 1
                return item.value
            self._stats.misses += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None,
        tags: Optional[Set[str]] = None,
        **kwargs,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间
            tags: 标签集合
            **kwargs: 额外参数

        Returns:
            是否设置成功
        """
        expire_at = None
        if expire:
            if isinstance(expire, int):
                expire = timedelta(seconds=expire)
            expire_at = datetime.now() + expire

        try:
            size = len(str(value).encode())
        except:
            size = 0

        item = CacheItem(value=value, expire_at=expire_at, size=size, tags=set(tags) if tags else set())

        async with self._lock:
            old_item = self._cache.get(key)
            self._cache[key] = item

            if not old_item:
                self._stats.total_items += 1
                self._stats.total_size += size
            else:
                self._stats.total_size = self._stats.total_size - old_item.size + size

            await self._notify_event("on_set", key, item)
            return True

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        async with self._lock:
            if key in self._cache:
                await self._delete_item(key, "delete")
                return True
            return False

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            键是否存在
        """
        async with self._lock:
            if item := self._cache.get(key):
                if item.is_expired():
                    await self._delete_item(key, "expire")
                    return False
                return True
            return False

    async def clear(self) -> bool:
        """
        清空缓存

        Returns:
            是否清空成功
        """
        async with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
            return True

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        批量获取多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        result = {}
        async with self._lock:
            for key in keys:
                if value := await self.get(key):
                    result[key] = value
        return result

    async def set_many(
        self, mapping: Dict[str, Any], expire: Optional[Union[int, timedelta]] = None, tags: Optional[Set[str]] = None
    ) -> bool:
        """
        批量设置多个缓存值

        Args:
            mapping: 键值对字典
            expire: 过期时间
            tags: 标签集合

        Returns:
            是否全部设置成功
        """
        async with self._lock:
            for key, value in mapping.items():
                await self.set(key, value, expire, tags)
        return True

    async def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的缓存键

        Args:
            pattern: 匹配模式

        Returns:
            删除的键数量
        """
        count = 0
        async with self._lock:
            keys = [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]
            for key in keys:
                if await self.delete(key):
                    count += 1
        return count

    async def delete_by_tags(self, tags: Set[str]) -> int:
        """
        删除指定标签的缓存键

        Args:
            tags: 标签集合

        Returns:
            删除的键数量
        """
        count = 0
        async with self._lock:
            keys = [key for key, item in self._cache.items() if item.tags & tags]
            for key in keys:
                if await self.delete(key):
                    count += 1
        return count

    async def get_by_pattern(self, pattern: str) -> Dict[str, Any]:
        """
        获取匹配模式的缓存值

        Args:
            pattern: 匹配模式

        Returns:
            键值对字典
        """
        result = {}
        async with self._lock:
            for key in self._cache:
                if fnmatch.fnmatch(key, pattern):
                    if value := await self.get(key):
                        result[key] = value
        return result

    async def get_by_tags(self, tags: Set[str]) -> Dict[str, Any]:
        """
        获取指定标签的缓存值

        Args:
            tags: 标签集合

        Returns:
            键值对字典
        """
        result = {}
        async with self._lock:
            for key, item in self._cache.items():
                if item.tags & tags:
                    if value := await self.get(key):
                        result[key] = value
        return result

    def on(self, event: str, handler: Callable) -> None:
        """
        注册事件处理器

        Args:
            event: 事件名称
            handler: 处理器函数
        """
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)

    async def _notify_event(self, event: str, key: str, item: CacheItem) -> None:
        """
        通知事件

        Args:
            event: 事件名称
            key: 缓存键
            item: 缓存项
        """
        for handler in self._event_handlers.get(event, []):
            try:
                await handler(key, item)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        async with self._lock:
            hit_ratio = (
                self._stats.hits / (self._stats.hits + self._stats.misses)
                if self._stats.hits + self._stats.misses > 0
                else 0
            )
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "hit_ratio": hit_ratio,
                "evictions": self._stats.evictions,
                "total_items": self._stats.total_items,
                "total_size": self._stats.total_size,
                "lock_stats": {
                    "acquisitions": self._stats.lock_acquisitions,
                    "releases": self._stats.lock_releases,
                    "timeouts": self._stats.lock_timeouts,
                },
            }

    async def get_lock(self, name: str, owner: str, timeout: Optional[int] = None, retry_interval: float = 0.1) -> bool:
        """
        获取锁

        Args:
            name: 锁名称
            owner: 锁持有者
            timeout: 超时时间
            retry_interval: 重试间隔

        Returns:
            是否获取成功
        """
        if name not in self._locks:
            self._locks[name] = LocalLock(name, timeout, retry_interval)

        lock = self._locks[name]
        success = await lock.acquire(owner)

        if success:
            self._stats.lock_acquisitions += 1
        else:
            self._stats.lock_timeouts += 1

        return success

    async def release_lock(self, name: str, owner: str) -> bool:
        """
        释放锁

        Args:
            name: 锁名称
            owner: 锁持有者

        Returns:
            是否释放成功
        """
        if lock := self._locks.get(name):
            if await lock.release(owner):
                self._stats.lock_releases += 1
                return True
        return False

    async def get_lock_info(self, name: str) -> Dict[str, Any]:
        """
        获取锁信息

        Args:
            name: 锁名称

        Returns:
            锁信息字典
        """
        if lock := self._locks.get(name):
            return {"owner": lock.owner, "expire_at": lock.expire_at, "waiters": lock.waiters}
        return {}

    async def delete_many(self, keys: List[str]) -> bool:
        """
        批量删除缓存值

        Args:
            keys: 缓存键列表

        Returns:
            是否全部删除成功
        """
        success = True
        async with self._lock:
            for key in keys:
                if not await self.delete(key):
                    success = False
        return success

    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """
        设置过期时间

        Args:
            key: 缓存键
            ttl: 过期时间

        Returns:
            是否设置成功
        """
        async with self._lock:
            if item := self._cache.get(key):
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                item.expire_at = datetime.now() + timedelta(seconds=ttl)
                return True
            return False

    async def ttl(self, key: str) -> Optional[int]:
        """
        获取剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数，None表示永不过期，-1表示不存在
        """
        async with self._lock:
            if item := self._cache.get(key):
                if item.expire_at is None:
                    return None
                if item.is_expired():
                    await self._delete_item(key, "expire")
                    return -1
                return int((item.expire_at - datetime.now()).total_seconds())
            return -1

    async def incr(self, key: str, delta: int = 1) -> int:
        """
        递增计数器

        Args:
            key: 缓存键
            delta: 增量值

        Returns:
            递增后的值
        """
        async with self._lock:
            if item := self._cache.get(key):
                try:
                    value = int(item.value) + delta
                    item.value = value
                    item.access()
                    return value
                except (TypeError, ValueError):
                    raise ValueError("值不是整数类型")
            value = delta
            await self.set(key, value)
            return value

    async def decr(self, key: str, delta: int = 1) -> int:
        """
        递减计数器

        Args:
            key: 缓存键
            delta: 减量值

        Returns:
            递减后的值
        """
        return await self.incr(key, -delta)

    async def get_status(self) -> Dict[str, Any]:
        """
        获取缓存状态信息

        Returns:
            状态信息字典
        """
        async with self._lock:
            stats = await self.get_stats()
            return {
                "backend_type": "local",
                "max_size": self.max_size,
                "current_size": len(self._cache),
                "stats": stats,
                "config": {
                    "cleanup_interval": self.cleanup_interval,
                },
            }


# 创建默认实例
local_backend = LocalCacheBackend()
