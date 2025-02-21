# 拦截器模块

## 模块简介

拦截器模块提供了请求和响应的拦截处理机制，用于实现请求预处理、响应后处理、全局异常处理等功能。支持灵活的拦截器链配置和自定义拦截器实现。

## 核心功能

1. 请求拦截
   - 请求验证
   - 参数处理
   - 认证授权
   - 日志记录
   - 请求转换

2. 响应拦截
   - 响应格式化
   - 数据转换
   - 错误处理
   - 响应压缩
   - 缓存控制

3. 异常拦截
   - 全局异常
   - 业务异常
   - 系统异常
   - 自定义异常
   - 错误响应

4. 上下文处理
   - 请求上下文
   - 用户上下文
   - 追踪上下文
   - 事务上下文
   - 资源上下文

## 使用方法

### 基础拦截器

```python
from core.interceptor import Interceptor, InterceptorChain

# 定义拦截器
class LoggingInterceptor(Interceptor):
    async def before_request(self, request):
        # 请求前处理
        request.start_time = time.time()
        logger.info(f"Processing request: {request.url}")
        
    async def after_request(self, request, response):
        # 请求后处理
        duration = time.time() - request.start_time
        logger.info(f"Request completed in {duration:.2f}s")
        return response

# 注册拦截器
interceptor_chain = InterceptorChain([
    LoggingInterceptor(),
    AuthenticationInterceptor(),
    RateLimitInterceptor()
])
```

### 异常拦截器

```python
from core.interceptor import ExceptionInterceptor

class GlobalExceptionInterceptor(ExceptionInterceptor):
    async def handle_exception(self, request, exc):
        if isinstance(exc, ValidationError):
            return JSONResponse(
                status_code=400,
                content={"error": str(exc)}
            )
        elif isinstance(exc, AuthenticationError):
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"}
            )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error"}
        )
```

### 上下文拦截器

```python
from core.interceptor import ContextInterceptor

class RequestContextInterceptor(ContextInterceptor):
    async def before_request(self, request):
        # 设置请求上下文
        request_id = generate_request_id()
        set_context("request_id", request_id)
        set_context("start_time", time.time())
        
    async def after_request(self, request, response):
        # 清理请求上下文
        clear_context()
        return response
```

## 配置选项

```python
INTERCEPTOR_CONFIG = {
    "enabled": True,
    "order": {
        "logging": 1,
        "authentication": 2,
        "rate_limit": 3,
        "context": 4
    },
    "logging": {
        "request": True,
        "response": True,
        "error": True
    },
    "authentication": {
        "exclude_paths": ["/health", "/metrics"],
        "token_location": "headers"
    },
    "rate_limit": {
        "enabled": True,
        "limit": 100,
        "window": 60
    },
    "context": {
        "preserve_context": False,
        "context_class": "RequestContext"
    }
}
```

## 最佳实践

1. 拦截器设计
   - 单一职责
   - 链式处理
   - 顺序控制
   - 性能优化

2. 异常处理
   - 统一处理
   - 分类处理
   - 错误转换
   - 日志记录

3. 上下文管理
   - 数据隔离
   - 资源管理
   - 生命周期
   - 清理机制

## 注意事项

1. 性能考虑
   - 处理时间
   - 内存使用
   - 并发处理
   - 资源消耗

2. 可靠性
   - 异常处理
   - 超时控制
   - 降级策略
   - 监控告警

3. 维护性
   - 代码组织
   - 配置管理
   - 测试覆盖
   - 文档更新 