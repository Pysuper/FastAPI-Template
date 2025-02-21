"""
多级缓存管理器模块

此模块提供了一个强大的多级缓存实现，支持：
    1. 本地内存缓存和Redis分布式缓存的多级架构
    2. 缓存预热和异步预加载
    3. 防止缓存击穿的分布式锁
    4. 缓存统计和监控
    5. 批量操作优化
    6. 自动过期和清理
    7. 错误处理和重试机制
    8. 序列化和压缩
    9. 事件通知
    10. 性能优化
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from core.cache.backends.memory import MemoryCache
from core.cache.backends.redis_ import RedisCache
from core.cache.config.config import CacheConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheStats:
    """缓存统计信息"""

    # 命中统计
    local_hits: int = 0
    local_misses: int = 0
    redis_hits: int = 0
    redis_misses: int = 0

    # 性能统计
    avg_get_time: float = 0.0
    avg_set_time: float = 0.0
    total_get_count: int = 0
    total_set_count: int = 0

    # 容量统计
    local_size: int = 0
    local_max_size: int = 0
    redis_size: int = 0

    # 错误统计
    errors: int = 0
    last_error_time: Optional[datetime] = None

    # 运行统计
    start_time: datetime = field(default_factory=datetime.now)
    last_cleanup_time: Optional[datetime] = None

    @property
    def uptime(self) -> float:
        """运行时间(秒)"""
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def local_hit_rate(self) -> float:
        """本地缓存命中率"""
        total = self.local_hits + self.local_misses
        return self.local_hits / total if total > 0 else 0.0

    @property
    def redis_hit_rate(self) -> float:
        """Redis缓存命中率"""
        total = self.redis_hits + self.redis_misses
        return self.redis_hits / total if total > 0 else 0.0


class MultiLevelCache(Generic[T]):
    """多级缓存管理器"""

    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        serializer: Optional[Callable[[T], str]] = None,
        deserializer: Optional[Callable[[str], T]] = None,
    ):
        """
        初始化多级缓存管理器

        Args:
            config: 缓存配置
            serializer: 自定义序列化函数
            deserializer: 自定义反序列化函数
        """
        self.config = config or CacheConfig()
        self.local = MemoryCache(
            maxsize=self.config.local_cache_size,
            ttl=self.config.local_cache_ttl,
        )
        self.redis = RedisCache(config=self.config)
        self.stats = CacheStats(local_max_size=self.config.local_cache_size)
        self._warmup_lock = asyncio.Lock()
        self._preload_tasks: Dict[str, asyncio.Task] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._event_handlers: Dict[str, List[Callable]] = {}
        self.serializer = serializer
        self.deserializer = deserializer

    async def init(self) -> None:
        """初始化缓存管理器"""
        await self.redis.init()
        self._start_cleanup_task()
        logger.info("多级缓存管理器初始化完成")

    async def close(self) -> None:
        """关闭缓存管理器"""
        # 取消清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 取消所有预加载任务
        for task in self._preload_tasks.values():
            task.cancel()
        await asyncio.gather(*self._preload_tasks.values(), return_exceptions=True)

        # 关闭Redis连接
        await self.redis.close()
        logger.info("多级缓存管理器已关闭")

    async def get(
        self,
        key: str,
        default: Optional[T] = None,
        update_local: bool = True,
    ) -> Optional[T]:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值
            update_local: 是否更新本地缓存

        Returns:
            缓存值或默认值
        """
        start_time = time.time()
        try:
            # 查询本地缓存
            value = await self.local.get(key)
            if value is not None:
                self.stats.local_hits += 1
                return self._deserialize(value)

            self.stats.local_misses += 1

            # 查询Redis缓存
            value = await self.redis.get(key)
            if value is not None:
                self.stats.redis_hits += 1
                if update_local:
                    # 更新本地缓存
                    await self.local.set(key, self._serialize(value), expire=self.config.local_cache_ttl)
                return self._deserialize(value)

            self.stats.redis_misses += 1
            return default

        except Exception as e:
            self._handle_error(e, "获取缓存失败")
            return default
        finally:
            # 更新性能统计
            self._update_get_stats(time.time() - start_time)

    async def set(
        self,
        key: str,
        value: T,
        expire: Optional[int] = None,
        local_only: bool = False,
        nx: bool = False,  # 键不存在时才设置
        xx: bool = False,  # 键存在时才设置
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)
            local_only: 是否只更新本地缓存
            nx: 键不存在时才设置
            xx: 键存在时才设置

        Returns:
            是否设置成功
        """
        start_time = time.time()
        try:
            success = True
            serialized_value = self._serialize(value)

            # 检查条件
            exists = await self.exists(key)
            if (nx and exists) or (xx and not exists):
                return False

            # 设置本地缓存
            local_expire = expire or self.config.local_cache_ttl
            success &= await self.local.set(key, serialized_value, expire=local_expire)

            # 设置Redis缓存
            if not local_only:
                success &= await self.redis.set(key, serialized_value, expire=expire or self.config.redis_cache_ttl)

            # 触发事件
            await self._trigger_event("set", key, value)
            return success

        except Exception as e:
            self._handle_error(e, "设置缓存失败")
            return False
        finally:
            # 更新性能统计
            self._update_set_stats(time.time() - start_time)

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            success = True
            # 删除本地缓存
            success &= await self.local.delete(key)
            # 删除Redis缓存
            success &= await self.redis.delete(key)
            # 触发事件
            await self._trigger_event("delete", key)
            return success
        except Exception as e:
            self._handle_error(e, "删除缓存失败")
            return False

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        try:
            # 检查本地缓存
            if await self.local.exists(key):
                return True
            # 检查Redis缓存
            return await self.redis.exists(key)
        except Exception as e:
            self._handle_error(e, "检查缓存键失败")
            return False

    async def clear(self, pattern: Optional[str] = None) -> bool:
        """
        清空缓存

        Args:
            pattern: 键模式，支持通配符

        Returns:
            是否清空成功
        """
        try:
            success = True
            # 清空本地缓存
            success &= await self.local.clear(pattern)
            # 清空Redis缓存
            success &= await self.redis.clear(pattern)
            # 触发事件
            await self._trigger_event("clear", pattern)
            return success
        except Exception as e:
            self._handle_error(e, "清空缓存失败")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """
        批量获取多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        result: Dict[str, T] = {}
        miss_keys: List[str] = []

        try:
            # 优先从本地缓存获取
            for key in keys:
                value = await self.local.get(key)
                if value is not None:
                    result[key] = self._deserialize(value)
                    self.stats.local_hits += 1
                else:
                    miss_keys.append(key)
                    self.stats.local_misses += 1

            # 从Redis获取未命中的键
            if miss_keys:
                redis_result = await self.redis.get_many(miss_keys)
                for key, value in redis_result.items():
                    if value is not None:
                        deserialized_value = self._deserialize(value)
                        result[key] = deserialized_value
                        self.stats.redis_hits += 1
                        # 更新本地缓存
                        await self.local.set(
                            key, self._serialize(deserialized_value), expire=self.config.local_cache_ttl
                        )
                    else:
                        self.stats.redis_misses += 1

            return result
        except Exception as e:
            self._handle_error(e, "批量获取缓存失败")
            return result

    async def set_many(
        self,
        mapping: Dict[str, T],
        expire: Optional[int] = None,
        local_only: bool = False,
    ) -> bool:
        """
        批量设置多个缓存值

        Args:
            mapping: 键值对字典
            expire: 过期时间(秒)
            local_only: 是否只更新本地缓存

        Returns:
            是否全部设置成功
        """
        try:
            success = True
            serialized_mapping = {k: self._serialize(v) for k, v in mapping.items()}

            # 设置本地缓存
            local_expire = expire or self.config.local_cache_ttl
            success &= await self.local.set_many(serialized_mapping, expire=local_expire)

            # 设置Redis缓存
            if not local_only:
                success &= await self.redis.set_many(serialized_mapping, expire=expire or self.config.redis_cache_ttl)

            # 触发事件
            await self._trigger_event("set_many", mapping)
            return success
        except Exception as e:
            self._handle_error(e, "批量设置缓存失败")
            return False

    async def delete_many(self, keys: List[str]) -> bool:
        """
        批量删除多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            是否全部删除成功
        """
        try:
            success = True
            # 删除本地缓存
            success &= await self.local.delete_many(keys)
            # 删除Redis缓存
            success &= await self.redis.delete_many(keys)
            # 触发事件
            await self._trigger_event("delete_many", keys)
            return success
        except Exception as e:
            self._handle_error(e, "批量删除缓存失败")
            return False

    async def get_or_set(
        self,
        key: str,
        value_generator: Callable[[], T],
        expire: Optional[int] = None,
        prevent_hotspot: bool = True,
    ) -> Optional[T]:
        """
        获取缓存值，如果不存在则设置

        Args:
            key: 缓存键
            value_generator: 值生成器函数
            expire: 过期时间(秒)
            prevent_hotspot: 是否防止缓存击穿

        Returns:
            缓存值
        """
        # 尝试获取缓存
        value = await self.get(key)
        if value is not None:
            return value

        if prevent_hotspot:
            # 使用分布式锁防止缓存击穿
            async with await self.redis.lock(f"lock:{key}"):
                # 双重检查
                value = await self.get(key)
                if value is not None:
                    return value

                # 生成新值
                try:
                    value = await value_generator()
                except Exception as e:
                    self._handle_error(e, "生成缓存值失败")
                    return None

                # 设置缓存
                await self.set(key, value, expire=expire)
                return value
        else:
            # 直接生成新值
            try:
                value = await value_generator()
            except Exception as e:
                self._handle_error(e, "生成缓存值失败")
                return None

            # 设置缓存
            await self.set(key, value, expire=expire)
            return value

    async def warmup(
        self,
        keys: List[str],
        loader: Callable[[List[str]], Dict[str, T]],
        expire: Optional[int] = None,
    ) -> None:
        """
        缓存预热

        Args:
            keys: 要预热的键列表
            loader: 加载数据的函数
            expire: 过期时间(秒)
        """
        async with self._warmup_lock:
            # 检查哪些键需要预热
            missing_keys = []
            for key in keys:
                if not await self.exists(key):
                    missing_keys.append(key)

            if not missing_keys:
                return

            # 加载数据
            try:
                data = await loader(missing_keys)
                # 批量更新缓存
                await self.set_many(data, expire=expire)
            except Exception as e:
                self._handle_error(e, "缓存预热失败")

    async def preload(
        self,
        key: str,
        loader: Callable[[], T],
        expire: Optional[int] = None,
        threshold: float = 0.9,
    ) -> None:
        """
        异步预加载缓存

        Args:
            key: 缓存键
            loader: 加载数据的函数
            expire: 过期时间(秒)
            threshold: 触发预加载的阈值(0-1)
        """
        # 检查是否已经在预加载
        if key in self._preload_tasks:
            return

        # 获取缓存过期时间
        ttl = await self.redis.ttl(key)
        if ttl is None:
            return

        # 计算是否需要预加载
        if ttl > 0 and ttl <= expire * threshold:
            # 创建预加载任务
            async def _preload():
                try:
                    # 加载新数据
                    value = await loader()
                    # 更新缓存
                    await self.set(key, value, expire=expire)
                except Exception as e:
                    self._handle_error(e, "预加载缓存失败")
                finally:
                    # 清理任务
                    self._preload_tasks.pop(key, None)

            self._preload_tasks[key] = asyncio.create_task(_preload())

    def on(self, event: str, handler: Callable) -> None:
        """
        注册事件处理器

        Args:
            event: 事件名称
            handler: 处理函数
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def _trigger_event(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        触发事件

        Args:
            event: 事件名称
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    await handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"事件处理失败: {event}, {str(e)}")

    def _start_cleanup_task(self) -> None:
        """启动清理任务"""

        async def _cleanup():
            while True:
                try:
                    await asyncio.sleep(self.config.cleanup_interval)
                    # 清理过期的本地缓存
                    await self.local.cleanup()
                    # 更新统计信息
                    self.stats.last_cleanup_time = datetime.now()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._handle_error(e, "缓存清理失败")

        self._cleanup_task = asyncio.create_task(_cleanup())

    def _handle_error(self, error: Exception, message: str) -> None:
        """
        处理错误

        Args:
            error: 异常对象
            message: 错误消息
        """
        self.stats.errors += 1
        self.stats.last_error_time = datetime.now()
        logger.error(f"{message}: {str(error)}")

    def _update_get_stats(self, duration: float) -> None:
        """
        更新获取操作的性能统计

        Args:
            duration: 操作耗时(秒)
        """
        self.stats.total_get_count += 1
        self.stats.avg_get_time = (
            self.stats.avg_get_time * (self.stats.total_get_count - 1) + duration
        ) / self.stats.total_get_count

    def _update_set_stats(self, duration: float) -> None:
        """
        更新设置操作的性能统计

        Args:
            duration: 操作耗时(秒)
        """
        self.stats.total_set_count += 1
        self.stats.avg_set_time = (
            self.stats.avg_set_time * (self.stats.total_set_count - 1) + duration
        ) / self.stats.total_set_count

    def _serialize(self, value: T) -> str:
        """
        序列化值

        Args:
            value: 原始值

        Returns:
            序列化后的字符串
        """
        if self.serializer:
            return self.serializer(value)
        return str(value)

    def _deserialize(self, value: str) -> T:
        """
        反序列化值

        Args:
            value: 序列化的字符串

        Returns:
            反序列化后的值
        """
        if self.deserializer:
            return self.deserializer(value)
        return value  # type: ignore


# 创建全局实例
multi_level_cache = MultiLevelCache()
