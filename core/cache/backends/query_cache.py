import hashlib
import json
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class QueryCache:
    """
    查询缓存管理器
    """

    def __init__(
        self,
        memory_cache=None,  # 内存缓存
        redis_cache=None,  # Redis缓存
        default_ttl: int = 300,  # 默认缓存时间(秒)
        enable_memory_cache: bool = True,  # 是否启用内存缓存
        enable_redis_cache: bool = True,  # 是否启用Redis缓存
        version: str = "1.0",  # 缓存版本
    ):
        self.memory_cache = memory_cache
        self.redis_cache = redis_cache
        self.default_ttl = default_ttl
        self.enable_memory_cache = enable_memory_cache
        self.enable_redis_cache = enable_redis_cache
        self.version = version

        # 缓存统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "redis_hits": 0,
            "sets": 0,
            "invalidations": 0,
        }

    def _generate_key(self, sql: str, params: Dict = None) -> str:
        """生成缓存键"""
        # 规范化参数
        if params is None:
            params = {}

        # 构建键内容
        key_content = {"sql": sql, "params": params, "version": self.version}

        # 序列化并计算MD5
        key_str = json.dumps(key_content, sort_keys=True)
        return f"query_cache:{hashlib.md5(key_str.encode()).hexdigest()}"

    async def get(self, sql: str, params: Dict = None) -> Tuple[bool, Any]:
        """获取缓存的查询结果"""
        key = self._generate_key(sql, params)

        # 先查内存缓存
        if self.enable_memory_cache and self.memory_cache:
            result = await self.memory_cache.get(key)
            if result is not None:
                self._stats["hits"] += 1
                self._stats["memory_hits"] += 1
                return True, result

        # 再查Redis缓存
        if self.enable_redis_cache and self.redis_cache:
            result = await self.redis_cache.get(key)
            if result is not None:
                self._stats["hits"] += 1
                self._stats["redis_hits"] += 1
                # 写入内存缓存
                if self.enable_memory_cache and self.memory_cache:
                    await self.memory_cache.set(key, result)
                return True, result

        self._stats["misses"] += 1
        return False, None

    async def set(self, sql: str, params: Dict, result: Any, ttl: Optional[int] = None):
        """设置缓存"""
        key = self._generate_key(sql, params)
        ttl = ttl or self.default_ttl

        # 写入内存缓存
        if self.enable_memory_cache and self.memory_cache:
            await self.memory_cache.set(key, result, ttl)

        # 写入Redis缓存
        if self.enable_redis_cache and self.redis_cache:
            await self.redis_cache.set(key, result, ttl)

        self._stats["sets"] += 1

    async def invalidate(self, sql: str, params: Dict = None):
        """失效缓存"""
        key = self._generate_key(sql, params)

        # 删除内存缓存
        if self.enable_memory_cache and self.memory_cache:
            await self.memory_cache.delete(key)

        # 删除Redis缓存
        if self.enable_redis_cache and self.redis_cache:
            await self.redis_cache.delete(key)

        self._stats["invalidations"] += 1

    async def clear(self):
        """清空缓存"""
        # 清空内存缓存
        if self.enable_memory_cache and self.memory_cache:
            await self.memory_cache.clear()

        # 清空Redis缓存
        if self.enable_redis_cache and self.redis_cache:
            await self.redis_cache.clear()

        self._stats["invalidations"] += 1

    def get_metrics(self) -> Dict:
        """获取缓存指标"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "enabled": {"memory_cache": self.enable_memory_cache, "redis_cache": self.enable_redis_cache},
            "version": self.version,
            "default_ttl": self.default_ttl,
            "stats": {**self._stats, "total_requests": total_requests, "hit_rate": hit_rate},
        }


class QueryCacheManager:
    """
    查询缓存管理器
    """

    def __init__(self, query_cache: QueryCache):
        self.query_cache = query_cache
