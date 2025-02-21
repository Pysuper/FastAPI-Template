"""
Redis缓存后端模块

此模块提供了基于Redis的缓存实现，支持：
    1. 连接池管理
    2. 序列化/反序列化
    3. 键前缀管理
    4. 批量操作优化
    5. 分布式锁
    6. 异步接口
    7. 监控统计
    8. 错误处理
    9. 自动重连
"""

import asyncio
import logging
import pickle
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

from core.cache.config.config import CacheConfig
from core.cache.exceptions import CacheError, CacheConnectionError
from core.cache.base.base import BaseCache
from core.cache.serializer import json_serializer
from core.loge.manager import logic as logger


@dataclass
class RedisStats:
    """
    Redis统计信息

    Attributes:
        hits: 命中次数
        misses: 未命中次数
        total_commands: 总命令数
        failed_commands: 失败命令数
        connected_time: 连接时间
        disconnected_time: 断开时间
        reconnect_count: 重连次数
    """

    hits: int = 0
    misses: int = 0
    total_commands: int = 0
    failed_commands: int = 0
    connected_time: float = 0
    disconnected_time: float = 0
    reconnect_count: int = 0


class RedisCache(BaseCache):
    """
    增强的Redis缓存实现

    特性：
        1. 连接池管理
        2. 多种序列化格式支持
        3. 自动重连机制
        4. 批量操作优化
        5. 分布式锁支持
        6. 监控统计
        7. 错误重试
        8. 键前缀管理
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        初始化Redis缓存

        Args:
            config: 缓存配置对象
        """
        super().__init__(config)
        self.config = config or CacheConfig()
        self._client: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._serializer = self._get_serializer()
        self._stats = RedisStats()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._reconnect_task: Optional[asyncio.Task] = None

    def _get_serializer(self):
        """获取序列化器"""
        if self.config.serialization_format == "json":
            return json_serializer
        elif self.config.serialization_format == "pickle":
            return pickle
        else:
            raise CacheError(f"不支持的序列化格式: {self.config.serialization_format}")

    async def init(self) -> None:
        """初始化Redis连接"""
        if self._initialized:
            return

        try:
            # 创建重试策略
            retry = Retry(ExponentialBackoff(), 3)

            # 创建客户端
            self._client = Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                db=self.config.redis.db,
                password=self.config.redis.password,
                max_connections=self.config.redis.max_connections,
                socket_timeout=self.config.redis.socket_timeout,
                socket_connect_timeout=self.config.redis.socket_connect_timeout,
                socket_keepalive=self.config.redis.socket_keepalive,
                health_check_interval=self.config.redis.health_check_interval,
                retry_on_timeout=self.config.redis.retry_on_timeout,
                retry=retry,
                decode_responses=True,
            )

            # 测试连接
            await self._client.ping()

            self._stats.connected_time = time.time()
            self._initialized = True
            logger.info("Redis cache initialized")

        except Exception as e:
            logger.error(f"Redis初始化失败: {e}")
            self._stats.disconnected_time = time.time()
            if self._client:
                await self._client.close()
                self._client = None
            raise CacheConnectionError(f"Redis连接失败: {e}")

    async def close(self) -> None:
        """关闭Redis连接"""
        if not self._initialized:
            return

        try:
            if self._reconnect_task:
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass
                self._reconnect_task = None

            if self._client:
                await self._client.close()
                self._client = None

            self._stats.disconnected_time = time.time()
            self._initialized = False
            logger.info("Redis cache closed")

        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")
            raise

    async def _ensure_connected(self) -> None:
        """确保Redis连接可用"""
        if not self._initialized or not self._client:
            await self.init()
            return

        try:
            await self._client.ping()
        except Exception as e:
            logger.error(f"Redis连接断开: {e}")
            self._stats.disconnected_time = time.time()
            self._stats.reconnect_count += 1
            await self.init()

    def _make_key(self, key: str) -> str:
        """生成带前缀的键名"""
        return f"{self.config.key_prefix}{key}"

    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            value = await self._client.get(self._make_key(key))
            if value is None:
                self._stats.misses += 1
                return default

            self._stats.hits += 1
            return self._serializer.loads(value)

        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"获取缓存值失败: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        exist: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)
            exist: 存在性条件(nx:不存在时设置/xx:存在时设置)
            **kwargs: 额外参数

        Returns:
            是否设置成功
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            key = self._make_key(key)
            value = self._serializer.dumps(value)

            if expire is None:
                expire = self.config.ttl

            if exist:
                if exist not in ("nx", "xx"):
                    raise CacheError(f"无效的exist选项: {exist}")
                return bool(
                    await self._client.set(
                        key,
                        value,
                        ex=expire,
                        nx=(exist == "nx"),
                        xx=(exist == "xx"),
                    )
                )

            return bool(await self._client.set(key, value, ex=expire))

        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"设置缓存值失败: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            return bool(await self._client.delete(self._make_key(key)))
        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"删除缓存值失败: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            键是否存在
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            exists = await self._client.exists(self._make_key(key))
            if exists:
                self._stats.hits += 1
            else:
                self._stats.misses += 1
            return bool(exists)
        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"检查缓存键失败: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间

        Args:
            key: 缓存键
            seconds: 过期时间(秒)

        Returns:
            是否设置成功
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            return bool(await self._client.expire(self._make_key(key), seconds))
        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"设置过期时间失败: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        获取剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数(-2:不存在/-1:永不过期/>=0:剩余秒数)
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            return await self._client.ttl(self._make_key(key))
        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"获取过期时间失败: {e}")
            return -2

    async def clear(self) -> bool:
        """
        清空缓存

        Returns:
            是否清空成功
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            pattern = self._make_key("*")
            keys = await self._client.keys(pattern)
            if keys:
                await self._client.delete(*keys)
            return True
        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"清空缓存失败: {e}")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        批量获取多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            # 转换键
            redis_keys = [self._make_key(key) for key in keys]

            # 批量获取
            values = await self._client.mget(redis_keys)

            # 转换结果
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._serializer.loads(value)
                    self._stats.hits += 1
                else:
                    self._stats.misses += 1

            return result

        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"批量获取缓存值失败: {e}")
            return {}

    async def set_many(
        self,
        mapping: Dict[str, Any],
        expire: Optional[int] = None,
        exist: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        批量设置多个缓存值

        Args:
            mapping: 键值对字典
            expire: 过期时间(秒)
            exist: 存在性条件
            **kwargs: 额外参数

        Returns:
            是否全部设置成功
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            # 转换键值对
            redis_mapping = {self._make_key(key): self._serializer.dumps(value) for key, value in mapping.items()}

            # 批量设置
            async with self._client.pipeline(transaction=True) as pipe:
                # 设置值
                await pipe.mset(redis_mapping)

                # 设置过期时间
                if expire is not None:
                    for key in redis_mapping:
                        await pipe.expire(key, expire)

                # 执行
                await pipe.execute()

            return True

        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"批量设置缓存值失败: {e}")
            return False

    async def delete_many(self, keys: List[str]) -> int:
        """
        批量删除多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            删除的键数量
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            # 转换键
            redis_keys = [self._make_key(key) for key in keys]

            # 批量删除
            return await self._client.delete(*redis_keys)

        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"批量删除缓存值失败: {e}")
            return 0

    async def incr(self, key: str, amount: int = 1) -> int:
        """
        递增值

        Args:
            key: 缓存键
            amount: 增加量

        Returns:
            增加后的值
        """
        await self._ensure_connected()
        self._stats.total_commands += 1

        try:
            return await self._client.incrby(self._make_key(key), amount)
        except Exception as e:
            self._stats.failed_commands += 1
            logger.error(f"递增缓存值失败: {e}")
            return 0

    async def decr(self, key: str, amount: int = 1) -> int:
        """
        递减值

        Args:
            key: 缓存键
            amount: 减少量

        Returns:
            减少后的值
        """
        return await self.incr(key, -amount)

    async def get_status(self) -> Dict[str, Any]:
        """
        获取缓存状态

        Returns:
            状态信息字典
        """
        if not self._client:
            return {"status": "not_connected", "stats": vars(self._stats)}

        try:
            # 获取Redis信息
            info = await self._client.info()

            # 合并统计信息
            return {
                "status": "connected",
                "stats": vars(self._stats),
                "redis_info": {
                    "version": info.get("redis_version"),
                    "used_memory": info.get("used_memory_human"),
                    "used_memory_peak": info.get("used_memory_peak_human"),
                    "total_connections_received": info.get("total_connections_received"),
                    "total_commands_processed": info.get("total_commands_processed"),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                },
            }

        except Exception as e:
            logger.error(f"获取缓存状态失败: {e}")
            return {"status": "error", "error": str(e), "stats": vars(self._stats)}

    async def scan_iter(self, match: Optional[str] = None, count: Optional[int] = None) -> AsyncIterator[str]:
        """
        扫描键的迭代器

        Args:
            match: 匹配模式
            count: 每次扫描的键数量

        Yields:
            符合条件的键
        """
        await self._ensure_connected()

        try:
            pattern = self._make_key(match if match else "*")
            async for key in self._client.scan_iter(match=pattern, count=count):
                yield key.removeprefix(self.config.prefix)
        except Exception as e:
            logger.error(f"扫描键失败: {e}")
            return

    async def get_lock(self, name: str, timeout: Optional[int] = None) -> bool:
        """
        获取分布式锁

        Args:
            name: 锁名称
            timeout: 超时时间(秒)

        Returns:
            是否获取成功
        """
        await self._ensure_connected()

        if timeout is None:
            timeout = self.config.lock_timeout

        try:
            key = self._make_key(f"lock:{name}")
            return bool(await self._client.set(key, 1, ex=timeout, nx=True))
        except Exception as e:
            logger.error(f"获取锁失败: {e}")
            return False

    async def release_lock(self, name: str) -> bool:
        """
        释放分布式锁

        Args:
            name: 锁名称

        Returns:
            是否释放成功
        """
        await self._ensure_connected()

        try:
            key = self._make_key(f"lock:{name}")
            return bool(await self._client.delete(key))
        except Exception as e:
            logger.error(f"释放锁失败: {e}")
            return False

    async def cleanup(self) -> bool:
        """
        清理过期的缓存数据

        Returns:
            bool: 清理是否成功
        """
        if not self._initialized or not self._client:
            return False

        try:
            # 使用 SCAN 命令遍历所有键
            async for key in self._client.scan_iter(match=f"{self.config.key_prefix}*"):
                try:
                    # 检查键是否过期
                    ttl = await self._client.ttl(key)
                    if ttl < 0:  # 已过期或没有设置过期时间
                        await self._client.delete(key)
                except Exception as e:
                    logger.error(f"清理键失败 {key}: {e}")
                    continue

            logger.info("缓存清理完成")
            return True

        except Exception as e:
            logger.error(f"缓存清理失败: {e}")
            return False


# 创建默认实例
redis_cache = RedisCache()
