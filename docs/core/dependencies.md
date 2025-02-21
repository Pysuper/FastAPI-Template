# 依赖注入模块

## 模块简介

依赖注入模块提供了一个灵活的依赖管理系统，用于管理应用程序中的服务、组件和资源之间的依赖关系。支持构造函数注入、属性注入和方法注入等多种注入方式。

## 核心功能

1. 依赖管理
   - 服务注册
   - 依赖解析
   - 生命周期管理
   - 作用域控制
   - 循环依赖处理

2. 注入方式
   - 构造函数注入
   - 属性注入
   - 方法注入
   - 接口注入
   - 配置注入

3. 特性支持
   - 懒加载
   - 单例模式
   - 工厂模式
   - 代理模式
   - 装饰器支持

## 使用方法

### 基础依赖

```python
from core.dependencies import Depends, Injectable
from core.db import Database
from core.cache import CacheManager

@Injectable()
class UserRepository:
    def __init__(self, db: Database = Depends()):
        self.db = db

@Injectable()
class UserService:
    def __init__(
        self,
        repository: UserRepository = Depends(),
        cache: CacheManager = Depends()
    ):
        self.repository = repository
        self.cache = cache
```

### 依赖装饰器

```python
from core.dependencies import inject, provider
from typing import Annotated

# 提供者装饰器
@provider
def get_database() -> Database:
    return Database()

# 注入装饰器
@inject
async def get_user(
    user_id: int,
    db: Annotated[Database, Depends()]
):
    return await db.query(User).filter_by(id=user_id).first()
```

### 作用域管理

```python
from core.dependencies import Scope, scoped

# 请求作用域
@scoped(Scope.REQUEST)
class RequestContext:
    def __init__(self):
        self.request_id = generate_request_id()

# 会话作用域
@scoped(Scope.SESSION)
class UserSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.login_time = datetime.now()
```

## 配置选项

```python
DEPENDENCIES_CONFIG = {
    "scopes": {
        "default": "singleton",
        "request": {
            "lifetime": "request"
        },
        "session": {
            "lifetime": "session"
        }
    },
    "providers": {
        "auto_register": True,
        "scan_packages": ["app.services", "app.repositories"]
    },
    "injection": {
        "allow_multiple": False,
        "strict_mode": True
    },
    "lifecycle": {
        "initialize_on_startup": True,
        "dispose_on_shutdown": True
    }
}
```

## 最佳实践

1. 依赖设计
   - 接口分离原则
   - 依赖倒置原则
   - 组件化设计
   - 松耦合原则

2. 生命周期管理
   - 合理使用作用域
   - 资源及时释放
   - 避免内存泄漏
   - 优化初始化过程

3. 性能优化
   - 懒加载策略
   - 缓存实例
   - 并发控制
   - 资源复用

## 注意事项

1. 依赖关系
   - 避免循环依赖
   - 控制依赖深度
   - 明确依赖关系
   - 文档化依赖

2. 性能考虑
   - 实例化开销
   - 内存占用
   - 并发访问
   - 资源限制

3. 可维护性
   - 清晰的结构
   - 统一的规范
   - 完善的测试
   - 版本兼容性 