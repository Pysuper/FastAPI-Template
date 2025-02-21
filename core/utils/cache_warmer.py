from typing import Any, Callable, Dict, Optional

from sqlalchemy.orm import Session

from core.cache.decorators import cache


class CacheWarmer:
    """缓存预热工具类"""

    @staticmethod
    async def warm_up(
        db: Session,
        cache_key: str,
        query_func: Callable,
        params: Optional[Dict[str, Any]] = None,
        expire: int = 3600,
    ) -> None:
        """
        预热缓存
        :param db: 数据库会话
        :param cache_key: 缓存键
        :param query_func: 查询函数
        :param params: 查询参数
        :param expire: 过期时间(秒)
        """
        # 执行查询
        if params is None:
            params = {}
        result = await query_func(**params)

        # 设置缓存
        if isinstance(result, (dict, list)):
            cache.set_json(cache_key, result, expire)
        else:
            cache.set_object(cache_key, result, expire)


warm_up_cache = CacheWarmer.warm_up
