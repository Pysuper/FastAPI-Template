import logging
from typing import Optional

import aioredis
from cache.base import QueryCacheManager, CacheConfig
from cache.backends.memory import MemoryCache
from cache.backends.redis_ import RedisCache

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务"""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.memory_cache: Optional[MemoryCache] = None
        self.redis_cache: Optional[RedisCache] = None
        self.cache_manager: Optional[QueryCacheManager] = None

    async def init(self, redis_url: Optional[str] = None):
        """初始化缓存服务"""
        # 初始化内存缓存
        if self.config.enable_memory_cache:
            self.memory_cache = MemoryCache(max_size=self.config.memory_cache_size)
            await self.memory_cache.start()
            logger.info("Memory cache initialized")

        # 初始化Redis缓存
        if self.config.enable_redis_cache and redis_url:
            redis = aioredis.from_url(redis_url)
            self.redis_cache = RedisCache(redis)
            # 测试Redis连接
            try:
                await redis.ping()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_cache = None

        # 初始化缓存管理器
        self.cache_manager = QueryCacheManager(
            memory_backend=self.memory_cache,
            redis_backend=self.redis_cache,
            config=self.config,
        )

    async def close(self):
        """关闭缓存服务"""
        if self.memory_cache:
            await self.memory_cache.stop()

        if self.redis_cache:
            await self.redis_cache.redis.close()

    async def clear(self):
        """清空所有缓存"""
        if self.cache_manager:
            await self.cache_manager.clear()

    def get_cache_manager(self) -> Optional[QueryCacheManager]:
        """获取缓存管理器"""
        return self.cache_manager

    async def get_stats(self) -> dict:
        """获取缓存统计信息"""
        stats = {
            "config": {
                "enable_memory_cache": self.config.enable_memory_cache,
                "enable_redis_cache": self.config.enable_redis_cache,
                "memory_cache_size": self.config.memory_cache_size,
                "memory_cache_expire": self.config.memory_cache_expire,
                "default_expire": self.config.default_expire,
            }
        }

        if self.memory_cache:
            stats["memory_cache"] = self.memory_cache.get_stats()

        if self.redis_cache:
            stats["redis_cache"] = await self.redis_cache.get_stats()

        return stats


# 全局缓存服务实例
cache_service = CacheService()
