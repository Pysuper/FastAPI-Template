# 中间件模块

## 模块简介

中间件模块提供了一系列可复用的中间件组件，用于在请求处理过程中实现横切关注点，如认证、日志记录、性能监控等。支持灵活的中间件配置和自定义扩展。

## 核心功能

1. 请求处理中间件
   - 认证中间件
   - CORS 中间件
   - 请求日志中间件
   - 性能监控中间件
   - 异常处理中间件

2. 安全中间件
   - CSRF 防护
   - XSS 防护
   - SQL 注入防护
   - 请求频率限制
   - IP 黑白名单

3. 功能增强中间件
   - 请求压缩
   - 响应缓存
   - 会话管理
   - 国际化支持
   - 静态文件处理

## 使用方法

### 中间件配置

```python
from fastapi import FastAPI
from core.middlewares import (
    AuthMiddleware,
    CORSMiddleware,
    RateLimitMiddleware,
    LoggingMiddleware
)

app = FastAPI()

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(
    RateLimitMiddleware,
    limit=100,
    window=60
)

app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)
```

### 自定义中间件

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 请求前处理
        print("处理请求前")
        
        # 调用下一个中间件
        response = await call_next(request)
        
        # 请求后处理
        print("处理请求后")
        
        return response
```

## 配置选项

```python
MIDDLEWARE_CONFIG = {
    "cors": {
        "allow_origins": ["*"],
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "allow_credentials": True
    },
    "rate_limit": {
        "limit": 100,
        "window": 60,
        "strategy": "sliding_window"
    },
    "auth": {
        "exclude_paths": ["/api/v1/auth/login", "/api/v1/auth/register"],
        "token_location": "headers"
    },
    "logging": {
        "exclude_paths": ["/health", "/metrics"],
        "log_request_body": False
    }
}
```

## 最佳实践

1. 中间件顺序
   - 认证/授权中间件放在前面
   - 日志中间件紧随其后
   - 性能相关中间件放在最后

2. 性能优化
   - 避免重复的中间件
   - 减少中间件数量
   - 优化中间件逻辑
   - 使用异步处理

3. 错误处理
   - 统一的错误处理机制
   - 合适的错误响应格式
   - 详细的错误日志记录

## 注意事项

1. 执行顺序
   - 中间件的添加顺序很重要
   - 注意依赖关系
   - 避免循环依赖

2. 性能影响
   - 监控中间件性能
   - 避免重复操作
   - 优化处理逻辑

3. 安全考虑
   - 验证请求来源
   - 防止中间件绕过
   - 保护敏感信息
   - 限制资源使用 