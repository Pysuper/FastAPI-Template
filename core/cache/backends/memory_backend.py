"""
内存缓存后端

此模块提供内存缓存后端实现，支持：
    1. 基础缓存操作
    2. 线程安全
    3. TTL支持
    4. LRU淘汰
    5. 统计信息
    6. 事件通知
    7. 容量限制
    8. 过期清理
    9. 性能监控
    10. 内存优化
    11. 并发控制
    12. 序列化支持
    13. 键前缀管理
    14. 错误处理
    15. 性能监控
"""

import asyncio
import logging
import pickle
import threading
import time
from collections import OrderedDict
from typing import Optional, Any, Dict, List, Union, TypeVar, Generic, Callable, NamedTuple

from core.cache.base.interface import CacheBackend
from core.cache.exceptions import CacheError

T = TypeVar("T")


class CacheItem(NamedTuple):
    """缓存项"""

    value: Any
    expire_at: Optional[float]
    created_at: float
    last_accessed: float
    hits: int
    size: int


class CacheStats:
    """缓存统计信息"""

    def __init__(self):
        self.hits: int = 0
        self.misses: int = 0
        self.evictions: int = 0
        self.size: int = 0
        self.items: int = 0
        self.oldest_item_age: float = 0
        self.newest_item_age: float = 0

    def to_dict(self) -> Dict[str, Union[int, float]]:
        """转换为字典"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "items": self.items,
            "oldest_item_age": self.oldest_item_age,
            "newest_item_age": self.newest_item_age,
        }


class MemoryCacheBackend(CacheBackend, Generic[T]):
    """增强的内存缓存后端实现"""

    def __init__(
        self,
        max_size: Optional[int] = None,
        max_items: Optional[int] = None,
        default_ttl: Optional[int] = None,
        cleanup_interval: int = 60,
        enable_stats: bool = True,
        serializer: Any = None,
        on_evict: Optional[Callable[[str, Any], None]] = None,
    ):
        """
        初始化内存缓存后端

        Args:
            max_size: 最大内存占用(字节)
            max_items: 最大条目数
            default_ttl: 默认过期时间(秒)
            cleanup_interval: 清理间隔(秒)
            enable_stats: 是否启用统计
            serializer: 序列化器
            on_evict: 淘汰回调函数
        """
        self._cache: OrderedDict[str, CacheItem] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats() if enable_stats else None
        self._max_size = max_size
        self._max_items = max_items
        self._default_ttl = default_ttl
        self._cleanup_interval = cleanup_interval
        self._serializer = serializer
        self._on_evict = on_evict
        self._cleanup_task: Optional[asyncio.Task] = None
        self._event_handlers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    async def init(self) -> None:
        """初始化缓存"""
        if self._cleanup_interval > 0:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.info("Started cleanup task")

    async def close(self) -> None:
        """关闭缓存"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Closed memory cache")

    async def get(self, key: str, default: T = None) -> Optional[T]:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            with self._lock:
                if key not in self._cache:
                    if self._stats:
                        self._stats.misses += 1
                    return default

                item = self._cache[key]
                now = time.time()

                # 检查是否过期
                if item.expire_at and item.expire_at <= now:
                    self._remove(key)
                    if self._stats:
                        self._stats.misses += 1
                    return default

                # 更新访问信息
                self._cache[key] = item._replace(last_accessed=now, hits=item.hits + 1)

                if self._stats:
                    self._stats.hits += 1

                # 移动到最新位置(LRU)
                self._cache.move_to_end(key)

                value = item.value
                if self._serializer:
                    value = self._serializer.deserialize(value)
                return value

        except Exception as e:
            self.logger.error(f"Get cache error: {str(e)}")
            raise CacheError(f"Get cache error: {str(e)}") from e

    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)
            nx: 键不存在时才设置
            xx: 键存在时才设置

        Returns:
            是否设置成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            with self._lock:
                exists = key in self._cache
                if (nx and exists) or (xx and not exists):
                    return False

                if self._serializer:
                    value = self._serializer.serialize(value)

                now = time.time()
                expire_at = now + (ttl or self._default_ttl) if ttl or self._default_ttl else None

                size = len(pickle.dumps(value))
                item = CacheItem(
                    value=value,
                    expire_at=expire_at,
                    created_at=now,
                    last_accessed=now,
                    hits=0,
                    size=size,
                )

                # 检查容量限制
                if self._max_size and size > self._max_size:
                    self.logger.warning(f"Item size {size} exceeds max size {self._max_size}")
                    return False

                # 淘汰旧数据
                while self._should_evict(size):
                    self._evict_one()

                self._cache[key] = item
                self._cache.move_to_end(key)

                if self._stats:
                    self._stats.size += size
                    self._stats.items += 1

                return True

        except Exception as e:
            self.logger.error(f"Set cache error: {str(e)}")
            raise CacheError(f"Set cache error: {str(e)}") from e

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            with self._lock:
                return bool(self._remove(key))
        except Exception as e:
            self.logger.error(f"Delete cache error: {str(e)}")
            raise CacheError(f"Delete cache error: {str(e)}") from e

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            with self._lock:
                if key not in self._cache:
                    return False

                item = self._cache[key]
                if item.expire_at and item.expire_at <= time.time():
                    self._remove(key)
                    return False

                return True

        except Exception as e:
            self.logger.error(f"Check exists error: {str(e)}")
            raise CacheError(f"Check exists error: {str(e)}") from e

    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间

        Args:
            key: 缓存键
            seconds: 过期时间(秒)

        Returns:
            是否设置成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            with self._lock:
                if key not in self._cache:
                    return False

                item = self._cache[key]
                expire_at = time.time() + seconds
                self._cache[key] = item._replace(expire_at=expire_at)
                return True

        except Exception as e:
            self.logger.error(f"Set expire error: {str(e)}")
            raise CacheError(f"Set expire error: {str(e)}") from e

    async def ttl(self, key: str) -> Optional[int]:
        """
        获取剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数，None表示永不过期，-1表示不存在

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            with self._lock:
                if key not in self._cache:
                    return -1

                item = self._cache[key]
                if not item.expire_at:
                    return None

                ttl = int(item.expire_at - time.time())
                if ttl <= 0:
                    self._remove(key)
                    return -1

                return ttl

        except Exception as e:
            self.logger.error(f"Get TTL error: {str(e)}")
            raise CacheError(f"Get TTL error: {str(e)}") from e

    async def clear(self, pattern: Optional[str] = None) -> bool:
        """
        清空缓存

        Args:
            pattern: 匹配模式,如: user:*

        Returns:
            是否清空成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            with self._lock:
                if pattern:
                    import re

                    regex = re.compile(pattern.replace("*", ".*"))
                    keys = [k for k in self._cache.keys() if regex.match(k)]
                    for key in keys:
                        self._remove(key)
                else:
                    self._cache.clear()
                    if self._stats:
                        self._stats.size = 0
                        self._stats.items = 0
                return True

        except Exception as e:
            self.logger.error(f"Clear cache error: {str(e)}")
            raise CacheError(f"Clear cache error: {str(e)}") from e

    async def get_stats(self) -> Optional[Dict[str, Union[int, float]]]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        if not self._stats:
            return None

        with self._lock:
            if self._cache:
                oldest = next(iter(self._cache.values()))
                newest = next(reversed(self._cache.values()))
                now = time.time()
                self._stats.oldest_item_age = now - oldest.created_at
                self._stats.newest_item_age = now - newest.created_at
            return self._stats.to_dict()

    def _should_evict(self, new_size: int) -> bool:
        """检查是否需要淘汰"""
        if self._max_items and len(self._cache) >= self._max_items:
            return True
        if self._max_size and self._stats:
            return self._stats.size + new_size > self._max_size
        return False

    def _evict_one(self) -> None:
        """淘汰一个缓存项"""
        if not self._cache:
            return

        # 获取最旧的项
        key, item = next(iter(self._cache.items()))
        self._remove(key)

        if self._stats:
            self._stats.evictions += 1

        if self._on_evict:
            try:
                self._on_evict(key, item.value)
            except Exception as e:
                self.logger.error(f"Eviction callback error: {str(e)}")

    def _remove(self, key: str) -> bool:
        """移除缓存项"""
        if key not in self._cache:
            return False

        item = self._cache.pop(key)
        if self._stats:
            self._stats.size -= item.size
            self._stats.items -= 1
        return True

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup error: {str(e)}")

    async def _cleanup_expired(self) -> None:
        """清理过期项"""
        now = time.time()
        with self._lock:
            expired = [key for key, item in self._cache.items() if item.expire_at and item.expire_at <= now]
            for key in expired:
                self._remove(key)
