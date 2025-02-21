"""
查询缓存管理器
实现查询结果缓存功能
"""

import hashlib
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Query

from core.config.manager import config_manager
from core.config.setting import settings


class QueryCache:
    """查询缓存管理器"""

    def __init__(self):
        self.config = config_manager.cache
        self.cache = settings.cache

    def _generate_cache_key(self, query: Query) -> str:
        """
        生成查询缓存键
        :param query: SQLAlchemy查询对象
        :return: 缓存键
        """
        # 获取查询语句
        statement = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

        # 计算哈希值
        return f"query_cache:{hashlib.md5(statement.encode()).hexdigest()}"

    async def get_cached_result(self, query: Query, model_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存的查询结果
        :param query: SQLAlchemy查询对象
        :param model_name: 模型名称
        :return: 缓存的结果或None
        """
        if not self.config.QUERY_CACHE_ENABLED:
            return None

        cache_key = self._generate_cache_key(query)
        cached_data = await self.cache.get(cache_key)

        if cached_data:
            return cached_data.get("results")
        return None

    async def cache_query_result(
        self,
        query: Query,
        model_name: str,
        results: List[Dict[str, Any]],
        expire: Optional[int] = None,
    ) -> None:
        """
        缓存查询结果
        :param query: SQLAlchemy查询对象
        :param model_name: 模型名称
        :param results: 查询结果
        :param expire: 过期时间(秒)
        """
        if not self.config.QUERY_CACHE_ENABLED:
            return

        cache_key = self._generate_cache_key(query)
        cache_data = {"model": model_name, "results": results, "timestamp": self.cache.get_timestamp()}

        # 如果没有指定过期时间，使用默认值
        if expire is None:
            expire = self.config.QUERY_CACHE_TTL

        await self.cache.set(cache_key, cache_data, expire=expire)

    async def invalidate_model_cache(self, model_name: str) -> None:
        """
        使指定模型的所有缓存失效
        :param model_name: 模型名称
        """
        if not self.config.QUERY_CACHE_ENABLED:
            return

        # 获取所有查询缓存键
        cache_keys = await self.cache.keys("query_cache:*")

        for key in cache_keys:
            cached_data = await self.cache.get(key)
            if cached_data and cached_data.get("model") == model_name:
                await self.cache.delete(key)

    async def clear_all_cache(self) -> None:
        """清除所有查询缓存"""
        if not self.config.QUERY_CACHE_ENABLED:
            return

        cache_keys = await self.cache.keys("query_cache:*")
        for key in cache_keys:
            await self.cache.delete(key)


# 创建查询缓存管理器实例
query_cache = QueryCache()

# 导出
__all__ = ["query_cache"]
