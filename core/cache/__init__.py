# """
# 缓存模块 (Cache Module)
#
# 这个模块提供了一个全面的缓存解决方案，支持多种缓存策略和高级特性。
#
# 主要特性:
#     - 多级缓存支持 (Memory, Redis, 混合模式)
#     - 灵活的序列化选项
#     - 分布式锁机制
#     - 监控和统计功能
#     - 声明式缓存装饰器
#     - 自动的键管理
#     - 异常处理机制
#
# 基本用法:
#     ```python
#     from custom.cache import cache, CacheManager
#
#     # 使用装饰器
#     @cache(ttl=300)
#     async def get_user(user_id: int):
#         return await db.get_user(user_id)
#
#     # 使用管理器
#     cache_manager = CacheManager()
#     await cache_manager.set("key", "value", ttl=300)
#     value = await cache_manager.get("key")
#     ```
#
# 高级用法:
#     ```python
#     from custom.cache import RedisLock, JsonSerializer
#
#     # 使用分布式锁
#     async with RedisLock("my_lock"):
#         # 临界区代码
#         pass
#
#     # 自定义序列化
#     cache_manager = CacheManager(serializer=JsonSerializer())
#     ```
# """
#
#
# # 导入缓存后端
# from .backends.memory import MemoryCache
# from .backends.memory_backend import MemoryCacheBackend
# from .backends.redis_ import RedisCache
# from .backends.redis_backend import RedisCacheBackend
# from .backends.local import LocalCache
# from .backends.local_backend import LocalCacheBackend
# from .backends.multi_level import MultiLevelCache
# from .backends.factory import cache_factory, CacheFactory
# from .backends.query_cache import QueryCache
# from .backends.redis_semaphore import RedisSemaphore
# from .backends.service import cache_service, CacheService
#
# # 导入核心接口
# from .base.interface import (
#     CacheBackend,
#     CacheInterface,
#     DistributedLock,
#     RateLimiter,
#     Serializer,
# )
#
# # 导入配置，因为这是基础依赖
# from .config.config import (
#     CacheConfig,
#     CacheLevel,
#     CacheStrategy,
#     MonitorConfig,
#     RedisConfig,
#     SerializationFormat,
# )
#
# # 导入装饰器
# from .decorators import (
#     cache,
#     cache_clear,
#     cache_if,
#     cache_invalidate,
#     cache_unless,
# )
#
# # 首先导入异常，因为其他模块可能依赖它
# from .exceptions import (
#     CacheConfigError,
#     CacheError,
#     CacheKeyError,
#     CacheLockError,
#     CacheSerializationError,
#     CacheTimeoutError,
# )
#
# # 导入工具和处理器
# from .handlers import (
#     ErrorHandler,
#     KeyHandler,
#     MetricsHandler,
# )
#
# # 导入锁实现
# from .lock.redis_lock import RedisLock
#
# # 最后导入管理器，因为它依赖前面的所有组件
# from .manager import (
#     CacheManager,
#     CacheMetrics,
#     CacheStats,
# )
#
# # 导入序列化器
# from .serializer import (
#     DefaultSerializer,
#     JsonSerializer,
#     MsgPackSerializer,
#     PickleSerializer,
# )
#
# __all__ = [
#     # 异常
#     "CacheError",
#     "CacheConfigError",
#     "CacheKeyError",
#     "CacheSerializationError",
#     "CacheLockError",
#     "CacheTimeoutError",
#     # 配置
#     "CacheConfig",
#     "CacheStrategy",
#     "CacheLevel",
#     "SerializationFormat",
#     "RedisConfig",
#     "MonitorConfig",
#     # 核心接口
#     "CacheBackend",
#     "Serializer",
#     "RateLimiter",
#     "DistributedLock",
#     "CacheInterface",
#     # 序列化器
#     "JsonSerializer",
#     "PickleSerializer",
#     "MsgPackSerializer",
#     "DefaultSerializer",
#     # 工具和处理器
#     "KeyHandler",
#     "ErrorHandler",
#     "MetricsHandler",
#     # 缓存后端
#     "MemoryCache",
#     "MemoryCacheBackend",
#     "RedisCache",
#     "RedisCacheBackend",
#     "LocalCache",
#     "LocalCacheBackend",
#     # 锁实现
#     "RedisLock",
#     # 装饰器
#     "cache",
#     "cache_invalidate",
#     "cache_clear",
#     "cache_unless",
#     "cache_if",
#     # 缓存管理
#     "CacheManager",
#     "CacheStats",
#     "CacheMetrics",
#     # 缓存工厂
#     "cache_factory",
#     "CacheFactory",
#     # 缓存服务
#     "cache_service",
#     "CacheService",
#     # 缓存查询
#     "QueryCache",
#     # 缓存信号量
#     "RedisSemaphore",
# ]
#
# # # 默认缓存管理器实例
# # from custom.config.setting import settings
# #
# # default_cache_manager = CacheManager(
# #     # backend_type=settings.cache.backend_type.value,
# #     # settings=settings.cache.settings,
# #     # prefix=settings.cache.key_prefix,
# #     # default_ttl=settings.cache.default_ttl,
# #     # serializer=settings.cache.serializer,
# #     # enable_stats=settings.cache.enable_metrics,
# #     # cleanup_interval=settings.cache.metrics_interval,
# #     # max_items=settings.cache.max_items,
# #     # max_memory=settings.cache.max_memory,
# #     backend_type=settings.cache.backend_type.value,
# #     settings=settings.cache.settings,
# #     serializer=settings.cache.serializer,
# #     prefix=settings.cache.key_prefix,
# #     **settings.get_backend_settings(),
# # )
