# 响应处理模块

## 模块简介

响应处理模块提供了统一的响应格式化和处理机制，用于规范化API响应格式，处理成功和错误响应，支持数据序列化、响应压缩、国际化等功能。

## 核心功能

1. 响应格式化
   - 统一响应结构
   - 数据序列化
   - 错误处理
   - 状态码管理
   - 消息模板

2. 数据处理
   - 数据转换
   - 字段过滤
   - 数据脱敏
   - 数据验证
   - 数据压缩

3. 国际化
   - 消息翻译
   - 语言切换
   - 时区处理
   - 货币格式
   - 数字格式

4. 响应增强
   - 分页处理
   - 排序支持
   - 缓存控制
   - 版本控制
   - 跨域支持

## 使用方法

### 基础响应

```python
from core.response import Response, ResponseSchema

# 成功响应
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await user_service.get_user(user_id)
    return Response.success(
        data=user,
        message="获取用户信息成功"
    )

# 错误响应
@app.post("/users")
async def create_user(user: UserCreate):
    try:
        user = await user_service.create_user(user)
        return Response.success(
            data=user,
            message="创建用户成功"
        )
    except ValidationError as e:
        return Response.error(
            code="VALIDATION_ERROR",
            message="数据验证失败",
            details=e.errors()
        )
```

### 分页响应

```python
from core.response import PaginatedResponse

@app.get("/posts")
async def list_posts(page: int = 1, size: int = 10):
    posts, total = await post_service.get_posts(page, size)
    return PaginatedResponse(
        data=posts,
        total=total,
        page=page,
        size=size
    )
```

### 自定义响应

```python
from core.response import CustomResponse

class FileResponse(CustomResponse):
    def __init__(self, file_path: str, filename: str = None):
        self.file_path = file_path
        self.filename = filename or os.path.basename(file_path)
        
    async def render(self):
        return StreamingResponse(
            file_iterator(self.file_path),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{self.filename}"'
            }
        )
```

## 配置选项

```python
RESPONSE_CONFIG = {
    "format": {
        "success_code": 0,
        "error_code_prefix": "E",
        "timestamp_field": "timestamp",
        "code_field": "code",
        "message_field": "message",
        "data_field": "data"
    },
    "pagination": {
        "page_field": "page",
        "size_field": "size",
        "total_field": "total",
        "default_size": 10,
        "max_size": 100
    },
    "serialization": {
        "datetime_format": "ISO8601",
        "ensure_ascii": False,
        "exclude_none": True
    },
    "compression": {
        "enabled": True,
        "min_size": 1024,
        "algorithms": ["gzip", "br"]
    }
}
```

## 最佳实践

1. 响应设计
   - 统一格式
   - 清晰结构
   - 错误码规范
   - 版本兼容

2. 性能优化
   - 数据压缩
   - 缓存控制
   - 按需加载
   - 响应裁剪

3. 安全处理
   - 数据脱敏
   - 输入验证
   - 跨域控制
   - 安全头部

## 注意事项

1. 数据处理
   - 类型转换
   - 空值处理
   - 大数据处理
   - 循环引用

2. 错误处理
   - 异常捕获
   - 错误提示
   - 日志记录
   - 调试信息

3. 兼容性
   - API版本
   - 客户端兼容
   - 向后兼容
   - 格式扩展 