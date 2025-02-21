# 装饰器模块

## 模块简介

装饰器模块提供了一系列可复用的装饰器，用于实现横切关注点的功能，如缓存、日志记录、性能监控、权限验证等。通过装饰器模式，实现代码的解耦和复用。

## 核心功能

1. 缓存装饰器
   - 结果缓存
   - 方法缓存
   - 参数缓存
   - 缓存失效
   - 缓存策略

2. 日志装饰器
   - 方法日志
   - 参数日志
   - 性能日志
   - 错误日志
   - 审计日志

3. 安全装饰器
   - 权限检查
   - 角色验证
   - 访问控制
   - 频率限制
   - 数据验证

4. 性能装饰器
   - 执行时间
   - 资源使用
   - 并发控制
   - 重试机制
   - 超时控制

## 使用方法

### 缓存装饰器

```python
from core.decorators import cached, cache_clear

# 方法结果缓存
@cached(ttl=3600)
async def get_user_info(user_id: int):
    return await db.query(User).filter_by(id=user_id).first()

# 带参数的缓存
@cached(ttl=3600, key_prefix="user_posts")
async def get_user_posts(user_id: int, page: int = 1):
    return await db.query(Post).filter_by(user_id=user_id).paginate(page)

# 清除缓存
@cache_clear(pattern="user_*")
async def update_user(user_id: int, data: dict):
    user = await db.query(User).filter_by(id=user_id).first()
    await user.update(data)
```

### 日志装饰器

```python
from core.decorators import logged, performance_log

# 方法日志
@logged()
async def create_order(user_id: int, items: list):
    # 创建订单逻辑
    pass

# 性能日志
@performance_log()
async def process_payment(order_id: str):
    # 处理支付逻辑
    pass

# 参数日志
@logged(params=True, result=True)
async def update_inventory(product_id: int, quantity: int):
    # 更新库存逻辑
    pass
```

### 安全装饰器

```python
from core.decorators import requires_auth, rate_limit

# 认证装饰器
@requires_auth
async def get_profile():
    return {"message": "Protected data"}

# 角色装饰器
@requires_roles(["admin", "manager"])
async def delete_user(user_id: int):
    await db.delete(user_id)

# 频率限制
@rate_limit(limit=100, window=60)
async def send_verification_code(phone: str):
    # 发送验证码逻辑
    pass
```

## 配置选项

```python
DECORATORS_CONFIG = {
    "cache": {
        "default_ttl": 3600,
        "key_prefix": "app:",
        "serializer": "json"
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "performance_threshold": 1.0
    },
    "security": {
        "token_location": "headers",
        "rate_limit": {
            "default_limit": 100,
            "default_window": 60
        }
    },
    "retry": {
        "max_retries": 3,
        "delay": 1,
        "backoff": 2,
        "exceptions": ["RequestError", "TimeoutError"]
    }
}
```

## 最佳实践

1. 装饰器设计
   - 单一职责
   - 可组合性
   - 参数灵活
   - 错误处理

2. 性能考虑
   - 最小化开销
   - 缓存策略
   - 异步支持
   - 资源控制

3. 使用规范
   - 清晰文档
   - 示例代码
   - 错误提示
   - 版本兼容

## 注意事项

1. 执行顺序
   - 装饰器顺序
   - 依赖关系
   - 副作用
   - 异常传播

2. 性能影响
   - 调用开销
   - 内存使用
   - 并发影响
   - 资源竞争

3. 维护性
   - 代码复杂度
   - 调试难度
   - 测试覆盖
   - 文档更新 