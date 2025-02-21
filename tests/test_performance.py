"""
缓存性能测试
"""
import asyncio
import time
from typing import List

import pytest

from core.cache.manager.factory import CacheFactory
from core.cache.config.settings import CacheStrategy


async def benchmark(func, *args, **kwargs):
    """性能测试函数"""
    start_time = time.time()
    result = await func(*args, **kwargs)
    end_time = time.time()
    return end_time - start_time, result
    
    
class TestCachePerformance:
    """缓存性能测试"""
    
    @pytest.fixture
    async def redis_cache(self):
        """Redis缓存fixture"""
        cache = CacheFactory.create(CacheStrategy.REDIS.value)
        await cache.init()
        yield cache
        await cache.clear()
        await cache.close()
        
    @pytest.fixture
    async def memory_cache(self):
        """内存缓存fixture"""
        cache = CacheFactory.create(CacheStrategy.MEMORY.value)
        yield cache
        await cache.clear()
        
    @pytest.fixture
    async def multi_level_cache(self):
        """多级缓存fixture"""
        cache = CacheFactory.create(CacheStrategy.BOTH.value)
        await cache.init()
        yield cache
        await cache.clear()
        await cache.close()
        
    async def test_set_performance(self, redis_cache, memory_cache, multi_level_cache):
        """测试写入性能"""
        data = {"key": "value"}
        
        # Redis缓存
        redis_time, _ = await benchmark(redis_cache.set, "key", data)
        print(f"\nRedis set time: {redis_time:.6f}s")
        
        # 内存缓存
        memory_time, _ = await benchmark(memory_cache.set, "key", data)
        print(f"Memory set time: {memory_time:.6f}s")
        
        # 多级缓存
        multi_time, _ = await benchmark(multi_level_cache.set, "key", data)
        print(f"Multi-level set time: {multi_time:.6f}s")
        
        assert memory_time < redis_time  # 内存缓存应该比Redis快
        
    async def test_get_performance(self, redis_cache, memory_cache, multi_level_cache):
        """测试读取性能"""
        data = {"key": "value"}
        
        # 预先写入数据
        await redis_cache.set("key", data)
        await memory_cache.set("key", data)
        await multi_level_cache.set("key", data)
        
        # Redis缓存
        redis_time, _ = await benchmark(redis_cache.get, "key")
        print(f"\nRedis get time: {redis_time:.6f}s")
        
        # 内存缓存
        memory_time, _ = await benchmark(memory_cache.get, "key")
        print(f"Memory get time: {memory_time:.6f}s")
        
        # 多级缓存(第一次从Redis获取)
        multi_time1, _ = await benchmark(multi_level_cache.get, "key")
        print(f"Multi-level get time (first): {multi_time1:.6f}s")
        
        # 多级缓存(第二次从本地获取)
        multi_time2, _ = await benchmark(multi_level_cache.get, "key")
        print(f"Multi-level get time (second): {multi_time2:.6f}s")
        
        assert memory_time < redis_time  # 内存缓存应该比Redis快
        assert multi_time2 < multi_time1  # 第二次获取应该更快
        
    async def test_batch_performance(self, redis_cache, memory_cache, multi_level_cache):
        """测试批量操作性能"""
        # 准备测试数据
        data = {f"key{i}": f"value{i}" for i in range(100)}
        keys = list(data.keys())
        
        # Redis缓存
        redis_set_time, _ = await benchmark(redis_cache.set_many, data)
        redis_get_time, _ = await benchmark(redis_cache.get_many, keys)
        print(f"\nRedis batch set time: {redis_set_time:.6f}s")
        print(f"Redis batch get time: {redis_get_time:.6f}s")
        
        # 内存缓存
        memory_set_time, _ = await benchmark(memory_cache.set_many, data)
        memory_get_time, _ = await benchmark(memory_cache.get_many, keys)
        print(f"Memory batch set time: {memory_set_time:.6f}s")
        print(f"Memory batch get time: {memory_get_time:.6f}s")
        
        # 多级缓存
        multi_set_time, _ = await benchmark(multi_level_cache.set_many, data)
        multi_get_time1, _ = await benchmark(multi_level_cache.get_many, keys)
        multi_get_time2, _ = await benchmark(multi_level_cache.get_many, keys)
        print(f"Multi-level batch set time: {multi_set_time:.6f}s")
        print(f"Multi-level batch get time (first): {multi_get_time1:.6f}s")
        print(f"Multi-level batch get time (second): {multi_get_time2:.6f}s")
        
        assert memory_set_time < redis_set_time  # 内存缓存批量写入应该更快
        assert memory_get_time < redis_get_time  # 内存缓存批量读取应该更快
        assert multi_get_time2 < multi_get_time1  # 第二次批量获取应该更快
        
    async def test_concurrent_performance(self, redis_cache, memory_cache, multi_level_cache):
        """测试并发性能"""
        async def concurrent_set(cache, prefix: str, count: int):
            """并发写入测试"""
            tasks = []
            for i in range(count):
                tasks.append(cache.set(f"{prefix}:{i}", f"value{i}"))
            return await asyncio.gather(*tasks)
            
        async def concurrent_get(cache, prefix: str, count: int):
            """并发读取测试"""
            tasks = []
            for i in range(count):
                tasks.append(cache.get(f"{prefix}:{i}"))
            return await asyncio.gather(*tasks)
            
        # 并发数
        concurrency = 1000
        
        # Redis缓存
        redis_set_time, _ = await benchmark(concurrent_set, redis_cache, "redis", concurrency)
        redis_get_time, _ = await benchmark(concurrent_get, redis_cache, "redis", concurrency)
        print(f"\nRedis concurrent set time: {redis_set_time:.6f}s")
        print(f"Redis concurrent get time: {redis_get_time:.6f}s")
        
        # 内存缓存
        memory_set_time, _ = await benchmark(concurrent_set, memory_cache, "memory", concurrency)
        memory_get_time, _ = await benchmark(concurrent_get, memory_cache, "memory", concurrency)
        print(f"Memory concurrent set time: {memory_set_time:.6f}s")
        print(f"Memory concurrent get time: {memory_get_time:.6f}s")
        
        # 多级缓存
        multi_set_time, _ = await benchmark(concurrent_set, multi_level_cache, "multi", concurrency)
        multi_get_time1, _ = await benchmark(concurrent_get, multi_level_cache, "multi", concurrency)
        multi_get_time2, _ = await benchmark(concurrent_get, multi_level_cache, "multi", concurrency)
        print(f"Multi-level concurrent set time: {multi_set_time:.6f}s")
        print(f"Multi-level concurrent get time (first): {multi_get_time1:.6f}s")
        print(f"Multi-level concurrent get time (second): {multi_get_time2:.6f}s")
        
    async def test_lock_performance(self, redis_cache):
        """测试锁性能"""
        async def acquire_release_lock(cache, key: str):
            """获取并释放锁"""
            await cache.lock(key)
            await cache.release_lock(key)
            
        # 测试获取释放锁的性能
        lock_time, _ = await benchmark(acquire_release_lock, redis_cache, "test_lock")
        print(f"\nLock acquire/release time: {lock_time:.6f}s")
        
        # 测试并发锁的性能
        async def concurrent_lock(cache, count: int):
            """并发锁测试"""
            tasks = []
            for i in range(count):
                tasks.append(acquire_release_lock(cache, f"lock:{i}"))
            return await asyncio.gather(*tasks)
            
        concurrency = 100
        concurrent_time, _ = await benchmark(concurrent_lock, redis_cache, concurrency)
        print(f"Concurrent lock time ({concurrency} locks): {concurrent_time:.6f}s")
        
    async def test_serialization_performance(self, redis_cache):
        """测试序列化性能"""
        # 准备不同大小的数据
        small_data = {"key": "value"}
        medium_data = {f"key{i}": f"value{i}" for i in range(100)}
        large_data = {f"key{i}": f"value{i}" for i in range(1000)}
        
        # 测试不同大小数据的序列化性能
        small_time, _ = await benchmark(redis_cache.set, "small", small_data)
        medium_time, _ = await benchmark(redis_cache.set, "medium", medium_data)
        large_time, _ = await benchmark(redis_cache.set, "large", large_data)
        
        print(f"\nSmall data serialization time: {small_time:.6f}s")
        print(f"Medium data serialization time: {medium_time:.6f}s")
        print(f"Large data serialization time: {large_time:.6f}s")
        
        assert small_time < medium_time < large_time  # 数据量越大，序列化时间应该越长 