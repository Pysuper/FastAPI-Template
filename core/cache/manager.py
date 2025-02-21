"""
缓存管理器模块

此模块提供全局缓存管理功能，支持：
    1. 多级缓存
    2. 分布式锁
    3. 缓存统计
    4. 缓存预热
    5. 缓存保护
    6. 自动过期
    7. 批量操作
    8. 事件通知
    9. 性能监控
    10. 错误处理
    11. JSON序列化
    12. 对象序列化
    13. 哈希表操作
    14. 计数器操作
    15. 模式匹配
"""

import asyncio
import json
import pickle
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

from redis import Redis

from cache.backends.redis_ import RedisCache
from cache.config.config import CacheConfig
from core.cache.backends.factory_backend import CacheBackendFactory
from core.cache.base.base import BaseCache
from core.cache.base.enums import CacheStrategy
from core.cache.exceptions import CacheError
from core.cache.serializer import SerializationFormat, create_serializer
from core.cache.setting import Settings
from core.config.setting import settings
from core.loge.manager import logic as logger

T = TypeVar("T")


@dataclass
class CacheStats:
    """缓存统计信息"""

    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_items: int = 0
    total_memory: int = 0
    evicted_items: int = 0
    expired_items: int = 0
    uptime: float = field(default_factory=time.time)
    last_cleanup: float = field(default_factory=time.time)

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

    @property
    def error_rate(self) -> float:
        """错误率"""
        total = self.hits + self.misses + self.errors
        return self.errors / total if total > 0 else 0

    @property
    def uptime_seconds(self) -> float:
        """运行时间(秒)"""
        return time.time() - self.uptime


class CacheManager(Generic[T]):
    """增强的异步缓存管理器"""

    def __init__(
        self,
        strategy: Union[str, CacheStrategy] = CacheStrategy.REDIS,
        settings: Optional[CacheConfig] = None,
        prefix: str = "",
        default_ttl: Optional[int] = None,
        serializer: Union[str, SerializationFormat] = SerializationFormat.JSON,
        enable_stats: bool = True,
        enable_memory_cache: bool = True,
        enable_redis_cache: bool = True,
        cleanup_interval: int = 300,
        max_items: Optional[int] = None,
        max_memory: Optional[int] = None,
    ):
        """
        初始化缓存管理器

        Args:
            strategy: 缓存策略
            settings: 配置对象
            prefix: 键前缀
            default_ttl: 默认过期时间(秒)
            serializer: 序列化格式
            enable_stats: 是否启用统计
            enable_memory_cache: 是否启用内存缓存
            enable_redis_cache: 是否启用Redis缓存
            cleanup_interval: 清理间隔(秒)
            max_items: 最大条目数
            max_memory: 最大内存(字节)
        """
        self.settings = settings or Settings()
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats
        self.enable_memory_cache = enable_memory_cache
        self.enable_redis_cache = enable_redis_cache
        self.cleanup_interval = cleanup_interval
        self.max_items = max_items
        self.max_memory = max_memory

        # 初始化后端
        if isinstance(strategy, str):
            strategy = CacheStrategy(strategy.lower())
        self.strategy = strategy

        self._backend: Optional[BaseCache] = RedisCache()
        self._stats = CacheStats() if enable_stats else None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._event_handlers: Dict[str, List[callable]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

        # 创建序列化器
        self.serializer = create_serializer(serializer)

    async def init(self, config: CacheConfig):
        """初始化缓存管理器"""
        try:
            # 创建后端
            self._backend = CacheBackendFactory.create(self.strategy, config)
            if self._backend:
                await self._backend.init()

            if self.cleanup_interval > 0:
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            print(" ✅ CacheManager")
            logger.info(f"缓存管理器初始化完成: {self.strategy.value}")
        except Exception as e:
            logger.error(f"缓存管理器初始化失败: {str(e)}")
            raise

    async def close(self):
        """关闭缓存管理器"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            if self._backend:
                try:
                    await self._backend.close()
                except Exception as e:
                    logger.error(f"关闭缓存后端失败: {str(e)}")

            logger.info("缓存管理器已关闭")
        except Exception as e:
            logger.error(f"关闭缓存管理器失败: {str(e)}")
            raise

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
            # 添加前缀
            key = self._add_prefix(key)

            # 获取值
            value = await self._backend.get(key)

            # 更新统计
            if self.enable_stats:
                if value is not None:
                    self._stats.hits += 1
                else:
                    self._stats.misses += 1

            # 触发事件
            await self._trigger_event("get", key, value)

            return value if value is not None else default

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"获取缓存失败: {key}, {str(e)}")
            raise CacheError(f"获取缓存失败: {str(e)}") from e

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取JSON缓存

        Args:
            key: 缓存键

        Returns:
            JSON数据或None
        """
        data = await self.get(key)
        return json.loads(data) if data else None

    async def set_json(self, key: str, value: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """
        设置JSON缓存

        Args:
            key: 缓存键
            value: JSON数据
            expire: 过期时间(秒)

        Returns:
            是否设置成功
        """
        return await self.set(key, json.dumps(value), expire)

    async def get_object(self, key: str) -> Optional[Any]:
        """
        获取Python对象缓存

        Args:
            key: 缓存键

        Returns:
            Python对象或None
        """
        if not self.enable_redis_cache:
            return None
        data = await self.pickle_redis.get(self._add_prefix(key))
        return pickle.loads(data) if data else None

    async def set_object(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置Python对象缓存

        Args:
            key: 缓存键
            value: Python对象
            expire: 过期时间(秒)

        Returns:
            是否设置成功
        """
        if not self.enable_redis_cache:
            return False
        return await self.pickle_redis.set(self._add_prefix(key), pickle.dumps(value), ex=expire)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
        serializer: Optional[Union[str, SerializationFormat]] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间
            serializer: 序列化格式
            nx: 键不存在时才设置
            xx: 键存在时才设置

        Returns:
            是否设置成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 检查条件
            exists = await self._backend.exists(key)
            if (nx and exists) or (xx and not exists):
                return False

            # 设置过期时间
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            ttl = ttl or self.default_ttl

            # 设置值
            success = await self._backend.set(key, value, ttl)

            # 更新统计
            if self.enable_stats and success:
                self._stats.total_items += 1

            # 触发事件
            await self._trigger_event("set", key, value, ttl)

            return success

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"设置缓存失败: {key}, {str(e)}")
            raise CacheError(f"设置缓存失败: {str(e)}") from e

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
            if not self._backend:
                logger.warning("缓存后端未初始化，跳过删除操作")
                return False

            # 添加前缀
            key = self._add_prefix(key)

            # 删除缓存
            success = await self._backend.delete(key)

            # 更新统计
            if self.enable_stats and success:
                self._stats.total_items -= 1

            # 触发事件
            await self._trigger_event("delete", key)

            return success

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"删除缓存失败: {key}, {str(e)}")
            # raise CacheError(f"删除缓存失败: {str(e)}") from e
            # 不抛出异常，返回False表示删除失败
            return False

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
            # 添加前缀
            key = self._add_prefix(key)

            # 检查存在
            return await self._backend.exists(key)

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"检查缓存键失败: {key}, {str(e)}")
            raise CacheError(f"检查缓存键失败: {str(e)}") from e

    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """设置过期时间

        Args:
            key: 缓存键
            ttl: 过期时间

        Returns:
            是否设置成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 设置过期时间
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            success = await self._backend.expire(key, ttl)

            # 触发事件
            await self._trigger_event("expire", key, ttl)

            return success

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"设置过期时间失败: {key}, {str(e)}")
            raise CacheError(f"设置过期时间失败: {str(e)}") from e

    async def ttl(self, key: str) -> Optional[int]:
        """获取剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数，None表示永不过期，-1表示不存在

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 获取过期时间
            return await self._backend.ttl(key)

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"获取过期时间失败: {key}, {str(e)}")
            raise CacheError(f"获取过期时间失败: {str(e)}") from e

    async def get_many(
        self,
        keys: List[str],
        serializer: Optional[Union[str, SerializationFormat]] = None,
    ) -> Dict[str, Any]:
        """批量获取缓存值

        Args:
            keys: 缓存键列表
            serializer: 序列化格式

        Returns:
            键值对字典

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            keys = [self._add_prefix(key) for key in keys]

            # 批量获取
            values = await self._backend.get_many(keys)

            # 更新统计
            if self.enable_stats:
                self._stats.hits += len(values)
                self._stats.misses += len(keys) - len(values)

            # 触发事件
            await self._trigger_event("get_many", keys, values)

            return values

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"批量获取缓存失败: {keys}, {str(e)}")
            raise CacheError(f"批量获取缓存失败: {str(e)}") from e

    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None,
        serializer: Optional[Union[str, SerializationFormat]] = None,
    ) -> bool:
        """批量设置缓存值

        Args:
            mapping: 键值对字典
            ttl: 过期时间
            serializer: 序列化格式

        Returns:
            是否全部设置成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            mapping = {self._add_prefix(k): v for k, v in mapping.items()}

            # 设置过期时间
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            ttl = ttl or self.default_ttl

            # 批量设置
            success = await self._backend.set_many(mapping, ttl)

            # 更新统计
            if self.enable_stats and success:
                self._stats.total_items += len(mapping)

            # 触发事件
            await self._trigger_event("set_many", mapping, ttl)

            return success

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"批量设置缓存失败: {mapping.keys()}, {str(e)}")
            raise CacheError(f"批量设置缓存失败: {str(e)}") from e

    async def delete_many(self, keys: List[str]) -> bool:
        """批量删除缓存值

        Args:
            keys: 缓存键列表

        Returns:
            是否全部删除成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            keys = [self._add_prefix(key) for key in keys]

            # 批量删除
            success = await self._backend.delete_many(keys)

            # 更新统计
            if self.enable_stats and success:
                self._stats.total_items -= len(keys)

            # 触发事件
            await self._trigger_event("delete_many", keys)

            return success

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"批量删除缓存失败: {keys}, {str(e)}")
            raise CacheError(f"批量删除缓存失败: {str(e)}") from e

    async def clear(self, prefix: Optional[str] = None) -> bool:
        """清空缓存

        Args:
            prefix: 键前缀，None表示清空所有

        Returns:
            是否清空成功

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            if prefix:
                prefix = self._add_prefix(prefix)

            # 清空缓存
            success = await self._backend.clear(prefix)

            # 更新统计
            if self.enable_stats and success:
                self._stats.total_items = 0

            # 触发事件
            await self._trigger_event("clear", prefix)

            return success

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"清空缓存失败: {prefix}, {str(e)}")
            raise CacheError(f"清空缓存失败: {str(e)}") from e

    async def incr(self, key: str, delta: int = 1) -> int:
        """递增计数器

        Args:
            key: 缓存键
            delta: 增量值

        Returns:
            递增后的值

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 递增计数器
            value = await self._backend.incr(key, delta)

            # 触发事件
            await self._trigger_event("incr", key, delta, value)

            return value

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"递增计数器失败: {key}, {str(e)}")
            raise CacheError(f"递增计数器失败: {str(e)}") from e

    async def decr(self, key: str, delta: int = 1) -> int:
        """递减计数器

        Args:
            key: 缓存键
            delta: 减量值

        Returns:
            递减后的值

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 递减计数器
            value = await self._backend.decr(key, delta)

            # 触发事件
            await self._trigger_event("decr", key, delta, value)

            return value

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"递减计数器失败: {key}, {str(e)}")
            raise CacheError(f"递减计数器失败: {str(e)}") from e

    async def get_or_set(
        self,
        key: str,
        default_func: Callable[[], Any],
        ttl: Optional[Union[int, timedelta]] = None,
        serializer: Optional[Union[str, SerializationFormat]] = None,
    ) -> Any:
        """获取或设置缓存值

        Args:
            key: 缓存键
            default_func: 默认值函数
            ttl: 过期时间
            serializer: 序列化格式

        Returns:
            缓存值

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 获取值
            value = await self._backend.get(key)

            # 更新统计
            if self.enable_stats:
                if value is not None:
                    self._stats.hits += 1
                else:
                    self._stats.misses += 1

            # 设置默认值
            if value is None:
                value = await default_func()
                if value is not None:
                    # 设置过期时间
                    if isinstance(ttl, timedelta):
                        ttl = int(ttl.total_seconds())
                    ttl = ttl or self.default_ttl

                    # 设置值
                    await self._backend.set(key, value, ttl)

                    # 更新统计
                    if self.enable_stats:
                        self._stats.total_items += 1

            # 触发事件
            await self._trigger_event("get_or_set", key, value)

            return value

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"获取或设置缓存失败: {key}, {str(e)}")
            raise CacheError(f"获取或设置缓存失败: {str(e)}") from e

    async def add_to_set(self, key: str, *values: Any) -> int:
        """添加到集合

        Args:
            key: 集合键
            values: 值列表

        Returns:
            新添加的元素数量

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 添加到集合
            count = await self._backend.sadd(key, *values)

            # 触发事件
            await self._trigger_event("add_to_set", key, values)

            return count

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"添加到集合失败: {key}, {str(e)}")
            raise CacheError(f"添加到集合失败: {str(e)}") from e

    async def remove_from_set(self, key: str, *values: Any) -> int:
        """从集合移除

        Args:
            key: 集合键
            values: 值列表

        Returns:
            移除的元素数量

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 从集合移除
            count = await self._backend.srem(key, *values)

            # 触发事件
            await self._trigger_event("remove_from_set", key, values)

            return count

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"从集合移除失败: {key}, {str(e)}")
            raise CacheError(f"从集合移除失败: {str(e)}") from e

    async def get_set_members(self, key: str) -> Set[Any]:
        """获取集合成员

        Args:
            key: 集合键

        Returns:
            成员集合

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 获取集合成员
            return await self._backend.smembers(key)

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"获取集合成员失败: {key}, {str(e)}")
            raise CacheError(f"获取集合成员失败: {str(e)}") from e

    async def get_set_length(self, key: str) -> int:
        """获取集合长度

        Args:
            key: 集合键

        Returns:
            集合长度

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            key = self._add_prefix(key)

            # 获取集合长度
            return await self._backend.scard(key)

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"获取集合长度失败: {key}, {str(e)}")
            raise CacheError(f"获取集合长度失败: {str(e)}") from e

    async def scan_keys(
        self,
        pattern: str = "*",
        count: int = 10,
    ) -> Tuple[int, List[str]]:
        """扫描键

        Args:
            pattern: 匹配模式
            count: 每次扫描的数量

        Returns:
            (游标, 键列表)

        Raises:
            CacheError: 缓存操作失败
        """
        try:
            # 添加前缀
            pattern = self._add_prefix(pattern)

            # 扫描键
            return await self._backend.scan(pattern, count)

        except Exception as e:
            if self.enable_stats:
                self._stats.errors += 1
            logger.error(f"扫描键失败: {pattern}, {str(e)}")
            raise CacheError(f"扫描键失败: {str(e)}") from e

    async def get_stats(self) -> Optional[CacheStats]:
        """获取统计信息

        Returns:
            统计信息对象
        """
        return self._stats if self.enable_stats else None

    def on(self, event: str, handler: callable):
        """注册事件处理器

        Args:
            event: 事件名称
            handler: 处理函数
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def _trigger_event(self, event: str, *args, **kwargs):
        """触发事件

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

    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                # 等待间隔时间
                await asyncio.sleep(self.cleanup_interval)

                # 执行清理
                await self._backend.cleanup()

                # 更新统计
                if self.enable_stats:
                    self._stats.last_cleanup = time.time()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理失败: {str(e)}")

    def _add_prefix(self, key: str) -> str:
        """添加键前缀

        Args:
            key: 原始键

        Returns:
            添加前缀后的键
        """
        return f"{self.prefix}:{key}" if self.prefix else key


class CacheManagerOld:
    """同步缓存管理器"""

    def __init__(self):
        self.redis = Redis(
            host=settings.cache.redis.host,
            port=settings.cache.redis.port,
            db=settings.cache.redis.db,
            password=settings.cache.redis.password,
            decode_responses=True,
        )
        self.pickle_redis = Redis(
            host=settings.cache.redis.host,
            port=settings.cache.redis.port,
            db=settings.cache.redis.db,
            password=settings.cache.redis.password,
            decode_responses=True,
        )

    def get(self, key: str) -> Optional[str]:
        """获取字符串缓存"""
        return self.redis.get(key)

    def set(self, key: str, value: str, expire: int = None) -> bool:
        """设置字符串缓存"""
        return self.redis.set(key, value, ex=expire)

    def get_json(self, key: str) -> Optional[dict]:
        """获取JSON缓存"""
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set_json(self, key: str, value: dict, expire: int = None) -> bool:
        """设置JSON缓存"""
        return self.redis.set(key, json.dumps(value), ex=expire)

    def get_object(self, key: str) -> Any:
        """获取Python对象缓存"""
        data = self.pickle_redis.get(key)
        return pickle.loads(data) if data else None

    def set_object(self, key: str, value: Any, expire: int = None) -> bool:
        """设置Python对象缓存"""
        return self.pickle_redis.set(key, pickle.dumps(value), ex=expire)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        return bool(self.redis.delete(key))

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return bool(self.redis.exists(key))

    def expire(self, key: str, seconds: int) -> bool:
        """设置缓存过期时间"""
        return bool(self.redis.expire(key, seconds))

    def ttl(self, key: str) -> int:
        """获取缓存剩余过期时间"""
        return self.redis.ttl(key)

    def incr(self, key: str, amount: int = 1) -> int:
        """递增缓存值"""
        return self.redis.incr(key, amount)

    def decr(self, key: str, amount: int = 1) -> int:
        """递减缓存值"""
        return self.redis.decr(key, amount)

    def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希表字段值"""
        return self.redis.hget(name, key)

    def hset(self, name: str, key: str, value: str) -> bool:
        """设置哈希表字段值"""
        return bool(self.redis.hset(name, key, value))

    def hmget(self, name: str, keys: list) -> list:
        """获取多个哈希表字段值"""
        return self.redis.hmget(name, keys)

    def hmset(self, name: str, mapping: dict) -> bool:
        """设置多个哈希表字段值"""
        return bool(self.redis.hmset(name, mapping))

    def hdel(self, name: str, *keys: str) -> int:
        """删除哈希表字段"""
        return self.redis.hdel(name, *keys)

    def hgetall(self, name: str) -> dict:
        """获取哈希表所有字段和值"""
        return self.redis.hgetall(name)

    def clear(self, pattern: str = None) -> int:
        """清空缓存
        Args:
            pattern: 匹配模式,如: user:*
        """
        if pattern:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        return self.redis.flushdb()


class CacheMetrics:
    """缓存指标收集器"""

    pass


# 创建缓存管理器实例
cache_manager = CacheManager(
    strategy=CacheStrategy.REDIS,
    settings=settings.cache,  # 使用全局配置中的缓存配置
    prefix="cache",
    default_ttl=300,
    enable_stats=True,
    enable_memory_cache=True,
    enable_redis_cache=True,
    cleanup_interval=300,
)
# cache_manager = CacheManager()
