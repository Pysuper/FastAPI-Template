from typing import Optional

from cache.base.base import BaseCache
from cache.base.enums import CacheStrategy
from cache.exceptions import CacheConfigError
from core.cache.backends.memory import MemoryCache
from core.cache.backends.multi_level import MultiLevelCache
from core.cache.backends.redis_ import RedisCache


class CacheFactory:
    """缓存工厂"""

    _instances = {}

    @classmethod
    def create(cls, strategy: str = CacheStrategy.REDIS.value, **kwargs) -> BaseCache:
        """
        创建缓存实例
        :param strategy: 缓存策略
        :param kwargs: 额外参数
        :return: 缓存实例
        """
        # 检查是否已存在实例
        if strategy in cls._instances:
            return cls._instances[strategy]

        # 创建新实例
        if strategy == CacheStrategy.REDIS.value:
            instance = RedisCache(**kwargs)
        elif strategy == CacheStrategy.MEMORY.value:
            instance = MemoryCache(**kwargs)
        elif strategy == CacheStrategy.BOTH.value:
            instance = MultiLevelCache(**kwargs)
        else:
            raise CacheConfigError(f"不支持的缓存策略: {strategy}")

        # 缓存实例
        cls._instances[strategy] = instance
        return instance

    @classmethod
    def get_instance(cls, strategy: str) -> Optional[BaseCache]:
        """
        获取缓存实例
        :param strategy: 缓存策略
        :return: 缓存实例
        """
        return cls._instances.get(strategy)

    @classmethod
    def clear_instances(cls):
        """清理所有实例"""
        cls._instances.clear()


cache_factory = CacheFactory()
