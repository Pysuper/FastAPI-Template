# 缓存模块

"""
缓存模块

这个模块提供了统一的缓存管理功能，包括：
- 多种缓存后端支持(Redis, 内存缓存等)
- 统一的缓存管理接口
- 可配置的序列化器
- 分布式锁支持
- 缓存装饰器
"""

## 目录结构
```
custom/cache/
├── __init__.py              # 模块初始化和导出
├── base/
│   ├── __init__.py
│   ├── interface.py         # 缓存接口定义
│   └── exceptions.py        # 自定义异常
├── backends/
│   ├── __init__.py
│   ├── memory.py           # 内存缓存实现
│   └── redis.py            # Redis缓存实现
├── serializers/
│   ├── __init__.py
│   ├── base.py             # 序列化器接口
│   ├── json.py             # JSON序列化器
│   └── pickle.py           # Pickle序列化器
├── manager/
│   ├── __init__.py
│   ├── factory.py          # 缓存管理器工厂
│   └── cache_manager.py    # 统一的缓存管理器
├── decorators/
│   ├── __init__.py
│   └── cache.py            # 缓存装饰器
└── utils/
    ├── __init__.py
    └── helpers.py          # 辅助函数
```

## 使用方法

### 基本用法

```python
from core.cache import CacheManager

# 创建缓存管理器
cache_manager = CacheManager()

# 设置缓存
await cache_manager.set("key", "value", expire=3600)

# 获取缓存
value = await cache_manager.get("key")

# 删除缓存
await cache_manager.delete("key")
```

### 使用装饰器

```python
from core.cache.decorators import cache

@cache(expire=3600)
async def get_user(user_id: int):
    # 函数实现
    pass
```

### 多级缓存

```python
from core.cache import MultiLevelCacheManager

# 创建多级缓存管理器
cache_manager = MultiLevelCacheManager([
    MemoryCacheBackend(),
    RedisCacheBackend()
])
```

### 分布式锁

```python
from core.cache import CacheManager

# 创建缓存管理器
cache_manager = CacheManager(backend_type="redis")

# 基本用法
async def example1():
    # 获取锁
    lock = cache_manager.get_lock("my_lock", expire=30)
    
    # 尝试获取锁
    if await lock.acquire():
        try:
            # 执行需要同步的操作
            pass
        finally:
            # 释放锁
            await lock.release()

# 使用上下文管理器
async def example2():
    async with cache_manager.get_lock("my_lock") as lock:
        # 执行需要同步的操作
        pass

# 高级用法
async def example3():
    lock = cache_manager.get_lock(
        name="my_lock",
        expire=30,          # 锁的过期时间
        timeout=5,          # 获取锁的超时时间
        retry_interval=0.1  # 重试间隔
    )
    
    if await lock.acquire():
        try:
            # 检查锁状态
            if await lock.is_locked():
                # 延长锁的过期时间
                await lock.extend(30)
                
            # 执行需要同步的操作
            pass
            
        finally:
            await lock.release()
```

## 配置项

- `CACHE_TYPE`: 缓存类型（memory/redis）
- `CACHE_PREFIX`: 缓存键前缀
- `CACHE_DEFAULT_TIMEOUT`: 默认过期时间
- `REDIS_URL`: Redis连接URL
- `REDIS_HOST`: Redis主机
- `REDIS_PORT`: Redis端口
- `REDIS_DB`: Redis数据库
- `REDIS_PASSWORD`: Redis密码

## 特性

- 支持多种缓存后端（内存、Redis）
- 支持多级缓存
- 灵活的序列化器
- 完善的异常处理
- 支持异步操作
- 支持批量操作
- 内置速率限制功能
- 装饰器支持 