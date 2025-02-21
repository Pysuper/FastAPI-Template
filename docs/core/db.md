# 数据库模块

## 模块简介

数据库模块提供了统一的数据库访问接口，支持多种数据库类型，包括关系型数据库和NoSQL数据库。实现了数据库连接池管理、事务管理、模型映射等核心功能。

## 核心功能

1. 数据库连接
   - 连接池管理
   - 多数据库支持
   - 读写分离
   - 故障转移
   - 连接监控

2. 事务管理
   - 事务控制
   - 事务隔离级别
   - 分布式事务
   - 事务传播
   - 事务回滚

3. 模型映射
   - ORM支持
   - 模型定义
   - 关系映射
   - 查询构建
   - 数据验证

4. 数据迁移
   - 版本控制
   - 自动迁移
   - 数据填充
   - 回滚支持
   - 迁移历史

## 使用方法

### 数据库连接

```python
from core.db import Database, get_db

# 创建数据库连接
db = Database(
    url="postgresql://user:pass@localhost:5432/dbname",
    pool_size=5,
    max_overflow=10
)

# 使用依赖注入获取数据库会话
async def get_users(db: Database = Depends(get_db)):
    return await db.query(User).all()
```

### 模型定义

```python
from core.db import Model, Column, relationship

class User(Model):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    posts = relationship("Post", back_populates="author")

class Post(Model):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
```

### 事务管理

```python
from core.db import transaction

# 使用事务装饰器
@transaction()
async def create_user_with_posts(db: Database, user_data: dict, posts_data: list):
    user = User(**user_data)
    await db.add(user)
    await db.flush()
    
    for post_data in posts_data:
        post = Post(author_id=user.id, **post_data)
        await db.add(post)
    
    await db.commit()

# 使用上下文管理器
async with db.transaction():
    user = User(username="test")
    await db.add(user)
    await db.commit()
```

## 配置选项

```python
DATABASE_CONFIG = {
    "default": {
        "url": "postgresql://user:pass@localhost:5432/dbname",
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "echo": False
    },
    "read_replica": {
        "url": "postgresql://readonly:pass@replica:5432/dbname",
        "pool_size": 10
    },
    "migration": {
        "auto_migrate": True,
        "version_table": "alembic_version",
        "directory": "migrations"
    }
}
```

## 最佳实践

1. 连接管理
   - 使用连接池
   - 及时释放连接
   - 监控连接状态
   - 设置超时时间

2. 查询优化
   - 使用适当的索引
   - 避免N+1查询
   - 优化JOIN操作
   - 使用批量操作

3. 事务处理
   - 合理的事务范围
   - 正确的隔离级别
   - 避免长事务
   - 处理并发冲突

## 注意事项

1. 性能优化
   - 连接池配置
   - 查询性能监控
   - 索引优化
   - 缓存策略

2. 数据安全
   - SQL注入防护
   - 数据加密
   - 访问控制
   - 审计日志

3. 可用性
   - 故障转移
   - 数据备份
   - 监控告警
   - 容量规划 