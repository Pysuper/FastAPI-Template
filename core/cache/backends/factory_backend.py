# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：factory_backend.py
@Author  ：PySuper
@Date    ：2025/1/2 12:58 
@Desc    ：Speedy factory_backend.py
"""

"""
缓存后端工厂

此模块提供缓存后端的创建工厂，用于避免循环导入
"""

import importlib
from typing import Optional, Type

from core.cache.base.base import BaseCache
from core.cache.base.enums import CacheStrategy
from core.cache.config.config import CacheConfig


class CacheBackendFactory:
    """缓存后端工厂"""

    _backend_map = {
        CacheStrategy.LOCAL: ("core.cache.backends.local_backend", "LocalCacheBackend"),
        CacheStrategy.MEMORY: ("core.cache.backends.memory_backend", "MemoryCacheBackend"),
        CacheStrategy.REDIS: ("core.cache.backends.redis_backend", "RedisCacheBackend"),
        CacheStrategy.MULTI: ("core.cache.backends.multi_level", "MultiLevelCache"),
    }

    @classmethod
    def create(cls, strategy: CacheStrategy, config: CacheConfig) -> Optional[BaseCache]:
        """
        创建缓存后端实例

        Args:
            strategy: 缓存策略
            config: 缓存配置

        Returns:
            缓存后端实例

        Raises:
            ValueError: 不支持的后端类型
        """
        if strategy == CacheStrategy.NONE:
            return None

        if strategy not in cls._backend_map:
            raise ValueError(f"不支持的后端类型: {strategy}")

        module_path, class_name = cls._backend_map[strategy]
        module = importlib.import_module(module_path)
        backend_class: Type[BaseCache] = getattr(module, class_name)

        return backend_class(config=config)
