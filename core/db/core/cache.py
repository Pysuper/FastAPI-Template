"""
@Project ：Speedy
@File    ：cache.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：数据库缓存管理模块

提供数据库缓存管理功能，包括:
    - 缓存初始化
    - 缓存清理
    - 缓存更新
    - 缓存监听
"""

import asyncio
from typing import Any, Optional

from sqlalchemy import event

# 全局缓存管理器
cache_manager: Optional[Any] = None


def init_cache_manager() -> None:
    """
    初始化缓存管理器
    在首次使用时延迟导入，避免循环依赖
    """
    global cache_manager
    if cache_manager is None:
        from core.cache.manager import cache_manager as cm

        cache_manager = cm


def setup_cache_events(model_class: Any) -> None:
    """
    设置缓存相关的事件监听器
    :param model_class: 模型类
    """

    @event.listens_for(model_class, "after_update", propagate=True)
    def clear_cache_after_update(mapper: Any, connection: Any, target: Any) -> None:
        """
        更新后清除缓存
        :param mapper: 映射器
        :param connection: 数据库连接
        :param target: 目标实例
        """
        if getattr(target, "_cache_enabled", False):
            init_cache_manager()
            cache_key = f"{target._cache_prefix}:id:{target.id}"
            asyncio.create_task(cache_manager.delete(cache_key))

    @event.listens_for(model_class, "after_delete", propagate=True)
    def clear_cache_after_delete(mapper: Any, connection: Any, target: Any) -> None:
        """
        删除后清除缓存
        :param mapper: 映射器
        :param connection: 数据库连接
        :param target: 目标实例
        """
        if getattr(target, "_cache_enabled", False):
            init_cache_manager()
            cache_key = f"{target._cache_prefix}:id:{target.id}"
            asyncio.create_task(cache_manager.delete(cache_key))


async def get_cached_model(model_class: Any, id: Any) -> Optional[Any]:
    """
    获取缓存的模型实例
    :param model_class: 模型类
    :param id: 实例ID
    :return: 模型实例或None
    """
    if not getattr(model_class, "_cache_enabled", False):
        return None

    init_cache_manager()
    cache_key = f"{model_class._cache_prefix}:id:{id}"
    cached = await cache_manager.get(cache_key)

    if cached:
        return model_class.from_dict(cached)
    return None


async def set_cached_model(instance: Any) -> None:
    """
    设置模型实例的缓存
    :param instance: 模型实例
    """
    if not getattr(instance, "_cache_enabled", False):
        return

    init_cache_manager()
    cache_key = f"{instance._cache_prefix}:id:{instance.id}"
    await cache_manager.set(cache_key, instance.to_dict(), expire=getattr(instance, "_cache_ttl", 3600))


async def delete_cached_model(instance: Any) -> None:
    """
    删除模型实例的缓存
    :param instance: 模型实例
    """
    if not getattr(instance, "_cache_enabled", False):
        return

    init_cache_manager()
    cache_key = f"{instance._cache_prefix}:id:{instance.id}"
    await cache_manager.delete(cache_key)
