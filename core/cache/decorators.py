"""
缓存装饰器模块

此模块提供了多种缓存装饰器实现，支持：
    1. 查询缓存
    2. 缓存失效
    3. Cache-Aside模式
    4. 通用缓存
    5. 批量操作
    6. 条件缓存
    7. 自定义键生成
    8. 多级缓存
"""

import asyncio
import functools
import hashlib
import inspect
import logging
import time
from datetime import timedelta
from typing import Callable, Optional, TypeVar, Union

from sqlalchemy.ext.asyncio import AsyncSession

from core.cache.base.enums import CacheStrategy, CacheMode
from core.cache.backends.query_cache import QueryCacheManager
from core.cache.key import CacheKey
from core.cache.manager import CacheManager
from core.cache.serializer import SerializationFormat

logger = logging.getLogger(__name__)

T = TypeVar("T")


def cached_query(
    prefix: str,
    expire: Optional[Union[int, timedelta]] = None,
    cache_null: bool = False,
    condition: Optional[Callable[..., bool]] = None,
    invalidate_on_update: bool = True,
    key_builder: Optional[Callable[..., str]] = None,
    strategy: Union[str, CacheStrategy] = CacheStrategy.REDIS,
    mode: Union[str, CacheMode] = CacheMode.READ_WRITE,
    serializer: Union[str, SerializationFormat] = SerializationFormat.JSON,
    tag: Optional[str] = None,
):
    """
    查询缓存装饰器

    Args:
        prefix: 缓存键前缀
        expire: 过期时间
        cache_null: 是否缓存空结果
        condition: 缓存条件函数
        invalidate_on_update: 更新时是否自动失效缓存
        key_builder: 自定义缓存键生成函数
        strategy: 缓存策略
        mode: 缓存模式
        serializer: 序列化格式
        tag: 缓存标签，用于分组管理

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 获取函数签名
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 绑定参数
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 获取缓存管理器和会话
            cache_manager = None
            session = None
            for arg in [*args, *kwargs.values()]:
                if isinstance(arg, QueryCacheManager):
                    cache_manager = arg
                elif isinstance(arg, AsyncSession):
                    session = arg

            if cache_manager is None:
                logger.warning(f"未找到缓存管理器: {func.__name__}")
                return await func(*args, **kwargs)

            # 检查缓存条件
            if condition and not condition(*args, **kwargs):
                return await func(*args, **kwargs)

            # 检查缓存模式
            if isinstance(mode, str):
                mode = CacheMode(mode.lower())

            # 生成缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 移除不需要的参数
                cache_args = {
                    k: v
                    for k, v in bound_args.arguments.items()
                    if not isinstance(v, (QueryCacheManager, AsyncSession))
                }
                cache_key = CacheKey.generate(prefix, **cache_args)

            # 添加标签
            if tag:
                await cache_manager.add_to_tag(tag, cache_key)

            # 尝试从缓存获取
            if mode != CacheMode.WRITE_ONLY:
                cached_value = await cache_manager.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"缓存命中: {func.__name__}:{cache_key}")
                    return cached_value

            # 执行查询
            start_time = time.time()
            result = await func(*args, **kwargs)
            query_time = time.time() - start_time

            # 缓存结果
            if mode != CacheMode.READ_ONLY and (result is not None or cache_null):
                await cache_manager.set(cache_key, result, expire, strategy=strategy, serializer=serializer)
                logger.debug(f"缓存结果: {func.__name__}:{cache_key}, " f"查询耗时: {query_time:.3f}s")

            return result

        # 添加缓存键生成方法
        wrapper.cache_key = lambda *args, **kwargs: (
            key_builder(*args, **kwargs) if key_builder else CacheKey.generate(prefix, *args, **kwargs)
        )

        # 添加缓存失效方法
        wrapper.invalidate = lambda cache_manager, *args, **kwargs: (
            cache_manager.delete(wrapper.cache_key(*args, **kwargs))
        )

        # 添加批量失效方法
        wrapper.invalidate_pattern = lambda cache_manager, pattern: (
            cache_manager.delete_pattern(f"{prefix}:{pattern}")
        )

        # 添加标签失效方法
        wrapper.invalidate_tag = lambda cache_manager, tag: (cache_manager.delete_by_tag(tag))

        return wrapper

    return decorator


def invalidate_cache(
    prefix: str,
    pattern: Optional[str] = None,
    tag: Optional[str] = None,
    condition: Optional[Callable[..., bool]] = None,
    strategy: Union[str, CacheStrategy] = CacheStrategy.REDIS,
):
    """缓存失效装饰器

    Args:
        prefix: 缓存键前缀
        pattern: 匹配模式
        tag: 缓存标签
        condition: 失效条件函数
        strategy: 缓存策略

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查失效条件
            if condition and not condition(*args, **kwargs):
                return await func(*args, **kwargs)

            # 获取缓存管理器
            cache_manager = None
            for arg in [*args, *kwargs.values()]:
                if isinstance(arg, QueryCacheManager):
                    cache_manager = arg
                    break

            if cache_manager is None:
                logger.warning(f"未找到缓存管理器: {func.__name__}")
                return await func(*args, **kwargs)

            # 执行函数
            start_time = time.time()
            result = await func(*args, **kwargs)
            exec_time = time.time() - start_time

            # 失效缓存
            if tag:
                await cache_manager.delete_by_tag(tag)
                logger.debug(f"按标签失效缓存: {tag}, " f"执行耗时: {exec_time:.3f}s")
            elif pattern:
                await cache_manager.delete_pattern(f"{prefix}:{pattern}", strategy=strategy)
                logger.debug(f"按模式失效缓存: {prefix}:{pattern}, " f"执行耗时: {exec_time:.3f}s")
            else:
                await cache_manager.delete_pattern(f"{prefix}:*", strategy=strategy)
                logger.debug(f"按前缀失效缓存: {prefix}, " f"执行耗时: {exec_time:.3f}s")

            return result

        return wrapper

    return decorator


def cache_aside(
    prefix: str,
    expire: Optional[Union[int, timedelta]] = None,
    cache_null: bool = False,
    condition: Optional[Callable[..., bool]] = None,
    strategy: Union[str, CacheStrategy] = CacheStrategy.REDIS,
    serializer: Union[str, SerializationFormat] = SerializationFormat.JSON,
    write_on_miss: bool = True,
    tag: Optional[str] = None,
):
    """Cache-Aside模式装饰器

    Args:
        prefix: 缓存键前缀
        expire: 过期时间
        cache_null: 是否缓存空结果
        condition: 缓存条件函数
        strategy: 缓存策略
        serializer: 序列化格式
        write_on_miss: 未命中时是否写入缓存
        tag: 缓存标签

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查缓存条件
            if condition and not condition(*args, **kwargs):
                return await func(*args, **kwargs)

            # 获取缓存管理器
            cache_manager = None
            for arg in [*args, *kwargs.values()]:
                if isinstance(arg, QueryCacheManager):
                    cache_manager = arg
                    break

            if cache_manager is None:
                logger.warning(f"未找到缓存管理器: {func.__name__}")
                return await func(*args, **kwargs)

            # 生成缓存键
            cache_key = CacheKey.generate(prefix, *args, **kwargs)

            # 添加标签
            if tag:
                await cache_manager.add_to_tag(tag, cache_key)

            # 尝试从缓存获取
            cached_value = await cache_manager.get(cache_key, strategy=strategy, serializer=serializer)
            if cached_value is not None:
                logger.debug(f"缓存命中: {func.__name__}:{cache_key}")
                return cached_value

            # 缓存未命中，执行查询
            start_time = time.time()
            result = await func(*args, **kwargs)
            query_time = time.time() - start_time

            # 异步写入缓存
            if write_on_miss and (result is not None or cache_null):
                asyncio.create_task(
                    cache_manager.set(cache_key, result, expire, strategy=strategy, serializer=serializer)
                )
                logger.debug(f"异步写入缓存: {func.__name__}:{cache_key}, " f"查询耗时: {query_time:.3f}s")

            return result

        return wrapper

    return decorator


def cache(
    key_prefix: str,
    ttl: Optional[int] = None,
    strategy: Union[str, CacheStrategy] = CacheStrategy.REDIS,
    serializer: Union[str, SerializationFormat] = SerializationFormat.JSON,
    key_builder: Optional[Callable[..., str]] = None,
    condition: Optional[Callable[..., bool]] = None,
    cache_null: bool = False,
    tag: Optional[str] = None,
):
    """通用缓存装饰器

    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间(秒)
        strategy: 缓存策略
        serializer: 序列化格式
        key_builder: 自定义键生成函数
        condition: 缓存条件函数
        cache_null: 是否缓存空结果
        tag: 缓存标签

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查缓存条件
            if condition and not condition(*args, **kwargs):
                return await func(*args, **kwargs)

            # 创建缓存管理器
            cache_manager = CacheManager()

            # 生成缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 默认使用函数名、参数和关键字参数生成键
                key_parts = [key_prefix, func.__module__, func.__name__, str(args), str(sorted(kwargs.items()))]
                key = ":".join(key_parts)
                cache_key = hashlib.md5(key.encode()).hexdigest()

            # 添加标签
            if tag:
                await cache_manager.add_to_tag(tag, cache_key)

            # 尝试从缓存获取
            cached_value = await cache_manager.get(cache_key, strategy=strategy, serializer=serializer)
            if cached_value is not None:
                logger.debug(f"缓存命中: {func.__name__}:{cache_key}")
                return cached_value

            # 执行函数
            start_time = time.time()
            result = await func(*args, **kwargs)
            exec_time = time.time() - start_time

            # 缓存结果
            if result is not None or cache_null:
                await cache_manager.set(cache_key, result, ttl, strategy=strategy, serializer=serializer)
                logger.debug(f"写入缓存: {func.__name__}:{cache_key}, " f"执行耗时: {exec_time:.3f}s")

            return result

        return wrapper

    return decorator


def batch_cache(
    key_prefix: str,
    batch_size: int = 100,
    ttl: Optional[int] = None,
    strategy: Union[str, CacheStrategy] = CacheStrategy.REDIS,
    serializer: Union[str, SerializationFormat] = SerializationFormat.JSON,
):
    """批量缓存装饰器

    Args:
        key_prefix: 缓存键前缀
        batch_size: 批处理大小
        ttl: 过期时间(秒)
        strategy: 缓存策略
        serializer: 序列化格式

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 创建缓存管理器
            cache_manager = CacheManager()

            # 获取要处理的项
            items = args[0] if args else kwargs.get("items", [])
            if not items:
                return await func(*args, **kwargs)

            # 分批处理
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]

                # 生成缓存键
                cache_keys = [f"{key_prefix}:{hashlib.md5(str(item).encode()).hexdigest()}" for item in batch]

                # 获取缓存值
                cached_values = await cache_manager.get_many(cache_keys, strategy=strategy, serializer=serializer)

                # 找出未命中的项
                missed_items = []
                missed_indices = []
                for j, (item, cache_key) in enumerate(zip(batch, cache_keys)):
                    if cache_key not in cached_values:
                        missed_items.append(item)
                        missed_indices.append(j)

                # 处理未命中的项
                if missed_items:
                    # 执行函数
                    missed_results = await func(missed_items, **kwargs)

                    # 更新缓存
                    to_cache = {cache_keys[idx]: result for idx, result in zip(missed_indices, missed_results)}
                    await cache_manager.set_many(to_cache, ttl, strategy=strategy, serializer=serializer)

                    # 合并结果
                    batch_results = []
                    missed_idx = 0
                    for j in range(len(batch)):
                        if j in missed_indices:
                            batch_results.append(missed_results[missed_idx])
                            missed_idx += 1
                        else:
                            batch_results.append(cached_values[cache_keys[j]])
                    results.extend(batch_results)
                else:
                    # 所有项都命中缓存
                    results.extend([cached_values[k] for k in cache_keys])

            return results

        return wrapper

    return decorator


def cache_decorator(prefix: str = "", expire: int = 3600, key_func=None):
    """缓存装饰器
    Args:
        prefix: 缓存键前缀
        expire: 过期时间(秒)
        key_func: 自定义缓存键生成函数
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                params = []
                params.extend([str(arg) for arg in args])
                params.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = f"{prefix}:{func.__name__}:{':'.join(params)}"

            # 获取缓存
            cached_data = cache.get_object(cache_key)
            if cached_data is not None:
                return cached_data

            # 执行函数
            result = await func(*args, **kwargs)

            # 设置缓存
            cache.set_object(cache_key, result, expire)

            return result

        return wrapper

    return decorator


def cache_invalidate():
    return None


def cache_clear():
    return None


def cache_unless():
    return None


def cache_if():
    return None


def clear_cache(pattern: str):
    """清除指定模式的缓存"""
    return cache.clear(pattern)
