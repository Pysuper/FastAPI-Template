"""
缓存单元测试
"""
import asyncio
import pytest
from datetime import timedelta

from core.cache.config.settings import CacheConfig, CacheStrategy
from core.cache.manager.factory import CacheFactory
from core.cache.backends.redis import RedisCache
from core.cache.backends.memory import MemoryCache
from core.cache.manager.multi_level import MultiLevelCache


@pytest.fixture
async def redis_cache():
    """Redis缓存fixture"""
    cache = RedisCache()
    await cache.init()
    yield cache
    await cache.clear()
    await cache.close()
    
    
@pytest.fixture
async def memory_cache():
    """内存缓存fixture"""
    cache = MemoryCache()
    yield cache
    await cache.clear()
    
    
@pytest.fixture
async def multi_level_cache():
    """多级缓存fixture"""
    cache = MultiLevelCache()
    await cache.init()
    yield cache
    await cache.clear()
    await cache.close()
    
    
class TestRedisCache:
    """Redis缓存测试"""
    
    async def test_set_get(self, redis_cache):
        """测试设置和获取"""
        await redis_cache.set("key", "value")
        assert await redis_cache.get("key") == "value"
        
    async def test_delete(self, redis_cache):
        """测试删除"""
        await redis_cache.set("key", "value")
        assert await redis_cache.exists("key")
        await redis_cache.delete("key")
        assert not await redis_cache.exists("key")
        
    async def test_expire(self, redis_cache):
        """测试过期"""
        await redis_cache.set("key", "value", expire=1)
        assert await redis_cache.get("key") == "value"
        await asyncio.sleep(1.1)
        assert await redis_cache.get("key") is None
        
    async def test_get_many(self, redis_cache):
        """测试批量获取"""
        await redis_cache.set_many({"key1": "value1", "key2": "value2"})
        values = await redis_cache.get_many(["key1", "key2"])
        assert values == {"key1": "value1", "key2": "value2"}
        
        
class TestMemoryCache:
    """内存缓存测试"""
    
    async def test_set_get(self, memory_cache):
        """测试设置和获取"""
        await memory_cache.set("key", "value")
        assert await memory_cache.get("key") == "value"
        
    async def test_delete(self, memory_cache):
        """测试删除"""
        await memory_cache.set("key", "value")
        assert await memory_cache.exists("key")
        await memory_cache.delete("key")
        assert not await memory_cache.exists("key")
        
    async def test_expire(self, memory_cache):
        """测试过期"""
        await memory_cache.set("key", "value", expire=1)
        assert await memory_cache.get("key") == "value"
        await asyncio.sleep(1.1)
        assert await memory_cache.get("key") is None
        
    async def test_get_many(self, memory_cache):
        """测试批量获取"""
        await memory_cache.set_many({"key1": "value1", "key2": "value2"})
        values = await memory_cache.get_many(["key1", "key2"])
        assert values == {"key1": "value1", "key2": "value2"}
        
        
class TestMultiLevelCache:
    """多级缓存测试"""
    
    async def test_set_get(self, multi_level_cache):
        """测试设置和获取"""
        await multi_level_cache.set("key", "value")
        assert await multi_level_cache.get("key") == "value"
        
    async def test_delete(self, multi_level_cache):
        """测试删除"""
        await multi_level_cache.set("key", "value")
        assert await multi_level_cache.exists("key")
        await multi_level_cache.delete("key")
        assert not await multi_level_cache.exists("key")
        
    async def test_expire(self, multi_level_cache):
        """测试过期"""
        await multi_level_cache.set("key", "value", expire=1)
        assert await multi_level_cache.get("key") == "value"
        await asyncio.sleep(1.1)
        assert await multi_level_cache.get("key") is None
        
    async def test_get_many(self, multi_level_cache):
        """测试批量获取"""
        await multi_level_cache.set_many({"key1": "value1", "key2": "value2"})
        values = await multi_level_cache.get_many(["key1", "key2"])
        assert values == {"key1": "value1", "key2": "value2"}
        
    async def test_cache_fallback(self, multi_level_cache):
        """测试缓存回退"""
        # 写入Redis
        await multi_level_cache.redis.set("key", "value")
        
        # 从本地缓存获取(应该为空)
        assert await multi_level_cache.local.get("key") is None
        
        # 从多级缓存获取(应该从Redis获取并写入本地缓存)
        assert await multi_level_cache.get("key") == "value"
        
        # 再次从本地缓存获取(应该已经写入)
        assert await multi_level_cache.local.get("key") == "value" 