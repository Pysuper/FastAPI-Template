# 数据仓储模块

## 模块简介

数据仓储模块提供了统一的数据访问接口，实现了数据持久化层的抽象，支持多种数据源、缓存策略、查询优化等功能。通过仓储模式，实现业务逻辑与数据访问的解耦。

## 核心功能

1. 基础操作
   - 增删改查
   - 批量操作
   - 事务支持
   - 关联查询
   - 条件过滤

2. 查询增强
   - 分页查询
   - 排序支持
   - 模糊搜索
   - 聚合统计
   - 复杂查询

3. 缓存策略
   - 查询缓存
   - 结果缓存
   - 缓存更新
   - 缓存失效
   - 缓存预热

4. 性能优化
   - 延迟加载
   - 批量处理
   - 查询优化
   - 连接池管理
   - 索引优化

## 使用方法

### 基础仓储

```python
from core.repositories import BaseRepository
from core.db import Database

class UserRepository(BaseRepository):
    def __init__(self, db: Database):
        super().__init__(db, model=User)
    
    async def find_by_username(self, username: str):
        return await self.find_one({"username": username})
    
    async def find_active_users(self):
        return await self.find_many({"status": "active"})
    
    async def update_last_login(self, user_id: int):
        await self.update(
            {"id": user_id},
            {"last_login": datetime.now()}
        )
```

### 高级查询

```python
from core.repositories import QueryBuilder

class PostRepository(BaseRepository):
    async def search_posts(self, keyword: str, category: str = None):
        query = QueryBuilder()\
            .filter(title__contains=keyword)\
            .order_by("-created_at")
        
        if category:
            query.filter(category=category)
        
        return await self.find_by_query(query)
    
    async def get_user_posts_stats(self, user_id: int):
        return await self.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ])
```

### 缓存支持

```python
from core.repositories import cached_repository

@cached_repository(ttl=3600)
class ProductRepository(BaseRepository):
    async def get_product_details(self, product_id: int):
        return await self.find_one_or_404({"id": product_id})
    
    @cached_repository.invalidate("product_*")
    async def update_product_stock(self, product_id: int, quantity: int):
        await self.update(
            {"id": product_id},
            {"stock": quantity}
        )
```

## 配置选项

```python
REPOSITORY_CONFIG = {
    "database": {
        "default_connection": "default",
        "max_connections": 100,
        "enable_logging": True
    },
    "cache": {
        "enabled": True,
        "default_ttl": 3600,
        "key_prefix": "repo:",
        "backend": "redis"
    },
    "query": {
        "max_limit": 1000,
        "default_page_size": 20,
        "enable_soft_delete": True
    },
    "performance": {
        "batch_size": 100,
        "enable_lazy_load": True,
        "min_in_memory_limit": 1000
    }
}
```

## 最佳实践

1. 仓储设计
   - 单一职责
   - 接口隔离
   - 充血模型
   - 领域驱动

2. 查询优化
   - 合理索引
   - 查询计划
   - N+1问题
   - 批量操作

3. 缓存策略
   - 缓存粒度
   - 更新策略
   - 一致性
   - 失效机制

## 注意事项

1. 性能考虑
   - 查询效率
   - 内存使用
   - 连接管理
   - 事务控制

2. 数据安全
   - 访问控制
   - 数据验证
   - SQL注入
   - 敏感数据

3. 可维护性
   - 代码组织
   - 错误处理
   - 测试覆盖
   - 文档完善 