"""
缓存管理器实例

此模块提供全局缓存管理器实例,用于避免循环导入
"""

import importlib
from typing import Optional, Any
from core.cache.base.manager_protocol import CacheManagerProtocol

# 全局缓存管理器实例
_cache_manager: Optional[CacheManagerProtocol] = None


def get_cache_manager() -> CacheManagerProtocol:
    """
    获取全局缓存管理器实例
    
    Returns:
        CacheManagerProtocol: 缓存管理器实例
    """
    global _cache_manager
    if _cache_manager is None:
        # 延迟导入CacheManager
        module = importlib.import_module('core.cache.manager')
        cache_manager_class = getattr(module, 'CacheManager')
        _cache_manager = cache_manager_class()
    return _cache_manager


def set_cache_manager(manager: CacheManagerProtocol) -> None:
    """
    设置全局缓存管理器实例
    
    Args:
        manager: 缓存管理器实例
    """
    global _cache_manager
    _cache_manager = manager 