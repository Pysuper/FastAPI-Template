# 缓存管理模块

## 模块简介

缓存管理模块提供了统一的缓存接口和多种缓存后端实现，支持内存缓存和 Redis 缓存，可以灵活配置缓存策略和失效机制。

## 核心功能

1. 多级缓存支持
   - 内存缓存（本地缓存）
   - Redis 缓存（分布式缓存）
   - 多级缓存联动

2. 缓存接口抽象
   - 统一的缓存操作接口
   - 可扩展的缓存后端
   - 缓存键前缀管理

3. 缓存策略
   - TTL（过期时间）控制
   - 缓存预热机制
   - 缓存穿透防护
   - 缓存击穿保护
   - 缓存雪崩预防

## 使用方法

### 基础缓存操作

```python
from core.cache import cache_manager

# 设置缓存
await cache_manager.set("key", "value", expire=3600)

# 获取缓存
value = await cache_manager.get("key")

# 删除缓存
await cache_manager.delete("key")

# 批量操作
await cache_manager.set_many({"key1": "value1", "key2": "value2"})
values = await cache_manager.get_many(["key1", "key2"])
```

### 缓存装饰器

```python
from core.cache.decorators import cached

@cached(ttl=3600, prefix="user")
async def get_user_info(user_id: int):
    # 业务逻辑
    pass
```

## 配置选项

```python
CACHE_CONFIG = {
    "default": {
        "backend": "redis",
        "host": "localhost",
        "port": your_port,
        "db": 0,
        "prefix": "speedy:",
        "ttl": 3600
    },
    "local": {
        "backend": "memory",
        "max_size": 1000,
        "ttl": 300
    }
}
```

## 最佳实践

1. 合理设置缓存过期时间
2. 使用合适的缓存键命名规范
3. 实现缓存预热机制
4. 添加缓存监控和统计
5. 定期清理过期缓存

## 注意事项

1. 缓存数据一致性
   - 及时更新或清除过期缓存
   - 处理缓存与数据库的同步

2. 性能考虑
   - 避免缓存大对象
   - 控制缓存数量
   - 合理设置过期时间

3. 安全性
   - 避免缓存敏感信息
   - 控制缓存访问权限
   - 防止缓存穿透攻击 