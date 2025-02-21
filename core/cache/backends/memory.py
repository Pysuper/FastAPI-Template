import asyncio
import fnmatch
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.cache.base.base import BaseCache
from core.cache.exceptions import CacheError
from core.cache.config.config import CacheConfig

logger = logging.getLogger(__name__)


@dataclass
class CacheItem:
    """
    缓存项

    Attributes:
        value: 缓存的值
        expire_at: 过期时间戳
        access_time: 最后访问时间
        access_count: 访问次数
        created_at: 创建时间
        size: 数据大小(字节)
    """

    value: Any
    expire_at: Optional[float] = None
    access_time: float = time.time()
    access_count: int = 0
    created_at: float = time.time()
    size: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        return self.expire_at is not None and time.time() >= self.expire_at

    def access(self) -> None:
        """更新访问信息"""
        self.access_time = time.time()
        self.access_count += 1


class MemoryCache(BaseCache):
    """
    增强的内存缓存实现

    特性：
        1. 支持TTL过期机制
        2. 线程安全
        3. LRU缓存淘汰
        4. 异步接口
        5. 模式匹配删除
        6. 分布式锁支持
        7. 统计信息收集
        8. 缓存预热
        9. 批量操作优化
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """初始化内存缓存

        Args:
            config: 缓存配置对象
        """
        super().__init__(config)
        self.config = config or CacheConfig()
        self._cache: Dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_items": 0,
            "total_size": 0,
        }
        self._initialized = False

    async def init(self) -> None:
        """初始化缓存系统"""
        if self._initialized:
            return

        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._initialized = True
        logger.info("Memory cache initialized")

    async def close(self) -> None:
        """关闭缓存系统"""
        if not self._initialized:
            return

        # 取消清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        # 清空缓存
        async with self._lock:
            self._cache.clear()
            self._stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "total_items": 0,
                "total_size": 0,
            }

        self._initialized = False
        logger.info("Memory cache closed")

    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        key = self._make_key(key)
        async with self._lock:
            if item := self._cache.get(key):
                if item.is_expired():
                    await self.delete(key)
                    self._stats["misses"] += 1
                    return default
                item.access()
                self._stats["hits"] += 1
                return item.value
            self._stats["misses"] += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        exist: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)
            exist: 存在性条件(nx:不存在时设置/xx:存在时设置)
            **kwargs: 额外参数

        Returns:
            是否设置成功
        """
        key = self._make_key(key)
        expire_at = time.time() + expire if expire is not None else None

        async with self._lock:
            # 检查缓存容量
            if len(self._cache) >= self.config.local_maxsize:
                await self._evict()

            # 检查存在性条件
            if exist == "nx" and key in self._cache:
                return False
            if exist == "xx" and key not in self._cache:
                return False

            # 计算数据大小
            try:
                size = len(str(value).encode())
            except:
                size = 0

            # 设置缓存
            item = CacheItem(value, expire_at, size=size)
            self._cache[key] = item
            self._stats["total_items"] = len(self._cache)
            self._stats["total_size"] += size
            return True

    async def delete(self, key: str) -> bool:
        """删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        key = self._make_key(key)
        async with self._lock:
            if item := self._cache.pop(key, None):
                self._stats["total_items"] = len(self._cache)
                self._stats["total_size"] -= item.size
                return True
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 缓存键

        Returns:
            键是否存在
        """
        key = self._make_key(key)
        async with self._lock:
            if item := self._cache.get(key):
                if item.is_expired():
                    await self.delete(key)
                    return False
                return True
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间

        Args:
            key: 缓存键
            seconds: 过期时间(秒)

        Returns:
            是否设置成功
        """
        key = self._make_key(key)
        async with self._lock:
            if item := self._cache.get(key):
                if item.is_expired():
                    await self.delete(key)
                    return False
                item.expire_at = time.time() + seconds
                return True
            return False

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数(-2:不存在/-1:永不过期/>=0:剩余秒数)
        """
        key = self._make_key(key)
        async with self._lock:
            if item := self._cache.get(key):
                if item.is_expired():
                    await self.delete(key)
                    return -2
                if item.expire_at is None:
                    return -1
                ttl = int(item.expire_at - time.time())
                return ttl if ttl > 0 else -2
            return -2

    async def clear(self) -> bool:
        """清空缓存

        Returns:
            是否清空成功
        """
        async with self._lock:
            self._cache.clear()
            self._stats["total_items"] = 0
            self._stats["total_size"] = 0
            return True

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        result = {}
        async with self._lock:
            for key in keys:
                key = self._make_key(key)
                if item := self._cache.get(key):
                    if item.is_expired():
                        await self.delete(key)
                        self._stats["misses"] += 1
                        continue
                    item.access()
                    result[key] = item.value
                    self._stats["hits"] += 1
                else:
                    self._stats["misses"] += 1
        return result

    async def set_many(
        self,
        mapping: Dict[str, Any],
        expire: Optional[int] = None,
        exist: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """批量设置多个缓存值

        Args:
            mapping: 键值对字典
            expire: 过期时间(秒)
            exist: 存在性条件
            **kwargs: 额外参数

        Returns:
            是否全部设置成功
        """
        success = True
        async with self._lock:
            for key, value in mapping.items():
                success &= await self.set(key, value, expire, exist, **kwargs)
        return success

    async def delete_many(self, keys: List[str]) -> int:
        """批量删除多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            删除的键数量
        """
        count = 0
        async with self._lock:
            for key in keys:
                if await self.delete(key):
                    count += 1
        return count

    async def incr(self, key: str, amount: int = 1) -> int:
        """递增值

        Args:
            key: 缓存键
            amount: 增加量

        Returns:
            增加后的值

        Raises:
            CacheError: 值不是整数时抛出
        """
        key = self._make_key(key)
        async with self._lock:
            if item := self._cache.get(key):
                if item.is_expired():
                    await self.delete(key)
                    item = None

            if item is None:
                value = amount
            else:
                try:
                    value = int(item.value) + amount
                except (TypeError, ValueError) as e:
                    raise CacheError(f"Value is not an integer: {e}")

            await self.set(key, value)
            return value

    async def decr(self, key: str, amount: int = 1) -> int:
        """递减值

        Args:
            key: 缓存键
            amount: 减少量

        Returns:
            减少后的值
        """
        return await self.incr(key, -amount)

    async def get_status(self) -> Dict[str, Any]:
        """获取缓存状态

        Returns:
            状态信息字典
        """
        async with self._lock:
            expired_items = sum(1 for item in self._cache.values() if item.is_expired())
            return {
                "total_items": self._stats["total_items"],
                "total_size": self._stats["total_size"],
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_ratio": (
                    self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                    if self._stats["hits"] + self._stats["misses"] > 0
                    else 0
                ),
                "evictions": self._stats["evictions"],
                "expired_items": expired_items,
                "max_size": self.config.local_maxsize,
                "cleanup_interval": self.config.memory.cleanup_interval,
            }

    def _make_key(self, key: str) -> str:
        """生成完整的缓存键

        Args:
            key: 原始键

        Returns:
            带前缀的完整键
        """
        return f"{self.config.prefix}{key}"

    async def _cleanup_loop(self) -> None:
        """清理循环任务"""
        while True:
            try:
                # 清理过期项
                async with self._lock:
                    for key in list(self._cache.keys()):
                        if self._cache[key].is_expired():
                            await self.delete(key)

                # 检查缓存大小
                if len(self._cache) >= self.config.local_maxsize:
                    await self._evict()

            except Exception as e:
                logger.error(f"Cache cleanup failed: {e}")

            await asyncio.sleep(self.config.memory.cleanup_interval)

    async def _evict(self) -> None:
        """驱逐缓存项

        使用LRU策略驱逐最近最少使用的项
        """
        if not self._cache:
            return

        # 按访问时间和访问次数排序
        items = sorted(
            self._cache.items(),
            key=lambda x: (x[1].access_time, x[1].access_count),
        )

        # 移除最旧的项
        async with self._lock:
            remove_count = len(items) // 4  # 每次移除1/4
            for key, item in items[:remove_count]:
                del self._cache[key]
                self._stats["total_items"] = len(self._cache)
                self._stats["total_size"] -= item.size
                self._stats["evictions"] += 1

    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存键

        Args:
            pattern: 匹配模式(支持Unix shell风格通配符)

        Returns:
            删除的键数量
        """
        count = 0
        async with self._lock:
            keys = list(self._cache.keys())
            for key in keys:
                if fnmatch.fnmatch(key, pattern):
                    if await self.delete(key):
                        count += 1
        return count


# 创建默认实例
memory_cache = MemoryCache()
