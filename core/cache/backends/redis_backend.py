"""
Redis缓存后端

此模块提供Redis缓存后端实现，支持：
    1. 基础缓存操作
    2. 分布式锁机制
    3. 信号量控制
    4. 乐观锁
    5. 悲观锁
    6. 行级锁
    7. 表级锁
    8. 可降级锁
    9. 公平锁
    10. 元数据管理
    11. 统计信息
    12. 序列化支持
    13. 键前缀管理
    14. 错误处理
    15. 性能监控
"""

import logging
import pickle
from datetime import datetime, timedelta
from pprint import pprint
from typing import Optional, Any, Dict, Set, List, Union, TypeVar, Generic, Callable

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from core.cache.config.config import CacheConfig
from core.config.load.base import BaseConfig
from core.cache.lock.redis_fair_lock import RedisFairLock
from core.cache.lock.redis_lock import RedisLock
from core.cache.lock.redis_lock_downgrade import RedisLockDowngrade
from core.cache.lock.redis_optimistic_lock import RedisOptimisticLock
from core.cache.lock.redis_pessimistic_lock import RedisPessimisticLock
from core.cache.lock.redis_row_lock import RedisRowLock
from core.cache.lock.redis_table_lock import RedisTableLock
from core.loge.manager import logic
from .redis_semaphore import RedisSemaphore
from ..base.interface import (
    CacheBackend,
    DistributedLock,
    DistributedSemaphore,
    DownGradableLock,
    OptimisticLock,
    PessimisticLock,
    RowLock,
    TableLock,
)

T = TypeVar("T")


class CacheInfo:
    """缓存项信息"""

    def __init__(
        self,
        key: str,
        value_type: str,
        size: int,
        created_at: datetime,
        expires_at: datetime,
        hits: int,
        last_accessed: datetime,
    ):
        self.key = key
        self.value_type = value_type
        self.size = size
        self.created_at = created_at
        self.expires_at = expires_at
        self.hits = hits
        self.last_accessed = last_accessed


class RedisCacheBackend(CacheBackend, Generic[T]):
    """
    Redis缓存后端实现，提供高级缓存功能
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        config: Optional[CacheConfig] = None,
        prefix: str = "cache:",
        default_ttl: int = 300,
        serializer: Any = None,
        enable_stats: bool = True,
        enable_metadata: bool = True,
    ):
        """
        初始化Redis缓存后端

        Args:
            redis_client: Redis客户端实例
            config: 配置对象
            prefix: 键前缀
            default_ttl: 默认过期时间(秒)
            serializer: 序列化器实例
            enable_stats: 是否启用统计
            enable_metadata: 是否启用元数据
        """
        if config:
            self.redis = Redis(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db,
                password=config.redis.password,
                decode_responses=True,
            )
            self.pickle_redis = Redis(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db,
                password=config.redis.password,
                decode_responses=False,
            )
            # 异步Redis客户端
            self.async_redis = AsyncRedis(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db,
                password=config.redis.password,
                decode_responses=True,
            )
            self.async_pickle_redis = AsyncRedis(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db,
                password=config.redis.password,
                decode_responses=False,
            )
            self.prefix = getattr(config, "prefix", prefix)
            self.default_ttl = getattr(config, "default_ttl", default_ttl)
            self.enable_stats = getattr(config, "enable_stats", enable_stats)
            self.enable_metadata = getattr(config, "enable_metadata", enable_metadata)
            self.serializer = getattr(config, "serializer", serializer)
        else:
            # 使用传入的Redis客户端
            self.redis = redis_client
            self.prefix = prefix
            self.default_ttl = default_ttl
            self.serializer = serializer
            self.enable_stats = enable_stats
            self.enable_metadata = enable_metadata

        print(" ✅ RedisCacheBackend")
        # self.logger = logging.getLogger(self.__class__.__name__)
        # 这样可以在每个模块中 使用不同的logger
        self.logger = logic

    def _make_key(self, key: str) -> str:
        """
        生成带前缀的键名

        Args:
            key: 原始键名

        Returns:
            带前缀的完整键名
        """
        return f"{self.prefix}{key}" if self.prefix else key

    async def init(self) -> None:
        """
        初始化缓存后端

        此方法在缓存管理器初始化时调用，用于：
        1. 建立Redis连接
        2. 初始化统计数据
        3. 清理过期元数据
        4. 设置监控任务
        """
        try:
            # 测试Redis连接
            await self.async_redis.ping()

            if self.enable_stats:
                # 初始化统计数据
                await self.async_redis.delete(f"{self.prefix}hits")

            if self.enable_metadata:
                # 清理过期元数据
                pattern = self._make_key("metadata:*")
                keys = await self.async_redis.keys(pattern)
                if keys:
                    await self.async_redis.delete(*keys)

            self.logger.debug("RedisCacheBackend initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize RedisCacheBackend: {str(e)}")
            raise

    async def get(self, key: str) -> Optional[T]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或None

        Raises:
            Exception: Redis操作异常
        """
        try:
            full_key = self._make_key(key)
            value = await self.async_redis.get(full_key)

            if value is not None:
                if self.enable_stats:
                    await self.async_redis.hincrby(f"{self.prefix}hits", key, 1)

                if self.serializer:
                    value = self.serializer.deserialize(value)
                elif isinstance(value, bytes):
                    value = pickle.loads(value)

            return value

        except Exception as e:
            self.logger.error(f"Redis get error: {str(e)}")
            raise

    async def set(self, key: str, value: T, expire: Optional[int] = None, nx: bool = False, xx: bool = False) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)
            nx: 键不存在时才设置
            xx: 键存在时才设置

        Returns:
            是否设置成功

        Raises:
            Exception: Redis操作异常
        """
        try:
            full_key = self._make_key(key)

            if self.serializer:
                value = self.serializer.serialize(value)
            elif not isinstance(value, (str, bytes, int, float)):
                value = pickle.dumps(value)

            # 设置缓存值
            result = await self.async_redis.set(full_key, value, ex=expire or self.default_ttl, nx=nx, xx=xx)

            if result and self.enable_metadata:
                # 记录元数据
                metadata = {
                    "type": type(value).__name__,
                    "size": len(pickle.dumps(value)) if not isinstance(value, (str, bytes)) else len(value),
                    "created_at": datetime.now().timestamp(),
                    "expires_at": (datetime.now() + timedelta(seconds=expire or self.default_ttl)).timestamp(),
                }
                await self.async_redis.hmset(f"{self.prefix}metadata:{key}", metadata)

            return bool(result)

        except Exception as e:
            self.logger.error(f"Redis set error: {str(e)}")
            raise

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功

        Raises:
            Exception: Redis操作异常
        """
        try:
            full_key = self._make_key(key)
            result = await self.async_redis.delete(full_key)

            if result:
                # 清理相关数据
                await self.async_redis.delete(f"{self.prefix}metadata:{key}")
                await self.async_redis.hdel(f"{self.prefix}hits", key)

            return bool(result)

        except Exception as e:
            self.logger.error(f"Redis delete error: {str(e)}")
            raise

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在

        Raises:
            Exception: Redis操作异常
        """
        try:
            full_key = self._make_key(key)
            return await self.async_redis.exists(full_key) > 0

        except Exception as e:
            self.logger.error(f"Redis exists error: {str(e)}")
            raise

    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间

        Args:
            key: 缓存键
            seconds: 过期时间(秒)

        Returns:
            是否设置成功

        Raises:
            Exception: Redis操作异常
        """
        try:
            full_key = self._make_key(key)
            result = await self.async_redis.expire(full_key, seconds)

            if result and self.enable_metadata:
                # 更新元数据
                await self.async_redis.hset(
                    f"{self.prefix}metadata:{key}",
                    "expires_at",
                    (datetime.now() + timedelta(seconds=seconds)).timestamp(),
                )

            return bool(result)

        except Exception as e:
            self.logger.error(f"Redis expire error: {str(e)}")
            raise

    async def ttl(self, key: str) -> int:
        """
        获取剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数

        Raises:
            Exception: Redis操作异常
        """
        try:
            full_key = self._make_key(key)
            return await self.async_redis.ttl(full_key)

        except Exception as e:
            self.logger.error(f"Redis ttl error: {str(e)}")
            raise

    async def clear(self, pattern: Optional[str] = None) -> bool:
        """
        清空缓存

        Args:
            pattern: 匹配模式,如: user:*

        Returns:
            是否清空成功

        Raises:
            Exception: Redis操作异常
        """
        try:
            if pattern:
                pattern = self._make_key(pattern)
                keys = await self.async_redis.keys(pattern)
                if keys:
                    await self.async_redis.delete(*keys)
                    # 清理相关数据
                    metadata_keys = [f"{self.prefix}metadata:{key}" for key in keys]
                    await self.async_redis.delete(*metadata_keys)
                    await self.async_redis.hdel(f"{self.prefix}hits", *keys)
            else:
                await self.async_redis.flushdb()
            return True

        except Exception as e:
            self.logger.error(f"Redis clear error: {str(e)}")
            raise

    async def get_info(self, key: str) -> Optional[CacheInfo]:
        """
        获取缓存项信息

        Args:
            key: 缓存键

        Returns:
            缓存信息对象

        Raises:
            Exception: Redis操作异常
        """
        try:
            if not await self.exists(key):
                return None

            metadata = await self.async_redis.hgetall(f"{self.prefix}metadata:{key}")
            hits = await self.async_redis.hget(f"{self.prefix}hits", key) or 0

            return CacheInfo(
                key=key,
                value_type=metadata.get("type", "unknown"),
                size=int(metadata.get("size", 0)),
                created_at=datetime.fromtimestamp(float(metadata.get("created_at", 0))),
                expires_at=datetime.fromtimestamp(float(metadata.get("expires_at", 0))),
                hits=int(hits),
                last_accessed=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Redis get info error: {str(e)}")
            raise

    def get_semaphore(
        self, name: str, count: int = 1, timeout: Optional[int] = None, retry_interval: float = 0.1, expire: int = 30
    ) -> DistributedSemaphore:
        """
        获取分布式信号量

        Args:
            name: 信号量名称
            count: 信号量计数
            timeout: 获取超时时间
            retry_interval: 重试间隔
            expire: 过期时间

        Returns:
            分布式信号量对象
        """
        return RedisSemaphore(
            redis_client=self.redis,
            name=self._make_key(name),
            count=count,
            timeout=timeout,
            retry_interval=retry_interval,
            expire=expire,
        )

    def get_lock(
        self,
        name: str,
        timeout: Optional[int] = None,
        retry_interval: float = 0.1,
        expire: int = 30,
        fair: bool = False,
    ) -> DistributedLock:
        """
        获取分布式锁

        Args:
            name: 锁名称
            timeout: 获取超时时间
            retry_interval: 重试间隔
            expire: 过期时间
            fair: 是否公平锁

        Returns:
            分布式锁对象
        """
        if fair:
            return RedisFairLock(
                redis_client=self.redis,
                name=self._make_key(name),
                timeout=timeout,
                retry_interval=retry_interval,
                expire=expire,
            )
        return RedisLock(
            redis_client=self.redis,
            name=self._make_key(name),
            timeout=timeout,
            retry_interval=retry_interval,
            expire=expire,
        )

    def get_downgradable_lock(
        self, name: str, timeout: Optional[int] = None, retry_interval: float = 0.1, expire: int = 30
    ) -> DownGradableLock:
        """
        获取可降级锁

        Args:
            name: 锁名称
            timeout: 获取超时时间
            retry_interval: 重试间隔
            expire: 过期时间

        Returns:
            可降级锁对象
        """
        return RedisLockDowngrade(
            redis_client=self.redis,
            name=self._make_key(name),
            timeout=timeout,
            retry_interval=retry_interval,
            expire=expire,
        )

    def get_optimistic_lock(self) -> OptimisticLock:
        """
        获取乐观锁实现

        Returns:
            乐观锁对象
        """
        return RedisOptimisticLock(redis_client=self.redis, serializer=self.serializer)

    def get_pessimistic_lock(
        self, name: str, timeout: Optional[int] = None, retry_interval: float = 0.1, expire: int = 30
    ) -> PessimisticLock:
        """
        获取悲观锁实现

        Args:
            name: 锁名称
            timeout: 获取超时时间
            retry_interval: 重试间隔
            expire: 过期时间

        Returns:
            悲观锁对象
        """
        return RedisPessimisticLock(
            redis_client=self.redis,
            name=self._make_key(name),
            timeout=timeout,
            retry_interval=retry_interval,
            expire=expire,
        )

    def get_row_lock(self) -> RowLock:
        """
        获取行级锁实现

        Returns:
            行级锁对象
        """
        return RedisRowLock(redis_client=self.redis, expire=30)

    def get_table_lock(self) -> TableLock:
        """
        获取表级锁实现

        Returns:
            表级锁对象
        """
        return RedisTableLock(redis_client=self.redis, expire=30)

    async def close(self) -> None:
        """
        关闭Redis连接
        """
        try:
            if hasattr(self, "async_redis") and self.async_redis:
                await self.async_redis.close()
            if hasattr(self, "async_pickle_redis") and self.async_pickle_redis:
                await self.async_pickle_redis.close()
            if hasattr(self, "redis") and self.redis:
                await self.redis.close()
            if hasattr(self, "pickle_redis") and self.pickle_redis:
                await self.pickle_redis.close()
            self.logger.info("Redis connections closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing Redis connections: {str(e)}")
            raise
