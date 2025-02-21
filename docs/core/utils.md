# 工具函数模块

## 模块简介

工具函数模块提供了一系列通用的工具函数和辅助方法，用于简化常见的编程任务，提高开发效率。包括字符串处理、日期时间、数据转换、加密解密等功能。

## 核心功能

1. 字符串处理
   - 字符串转换
   - 模板渲染
   - 正则匹配
   - 编码解码
   - 格式化

2. 日期时间
   - 时间转换
   - 日期计算
   - 时区处理
   - 格式化输出
   - 时间比较

3. 数据处理
   - 类型转换
   - 数据验证
   - 序列化
   - 深拷贝
   - 数据合并

4. 加密安全
   - 哈希计算
   - 加密解密
   - 签名验证
   - 随机生成
   - 敏感信息处理

## 使用方法

### 字符串工具

```python
from core.utils.string import StringUtils

# 驼峰转下划线
result = StringUtils.camel_to_snake("getUserName")  # get_user_name

# 下划线转驼峰
result = StringUtils.snake_to_camel("user_profile")  # userProfile

# 模板渲染
template = "Hello, {name}! Welcome to {site}."
result = StringUtils.render_template(template, name="John", site="Example")

# 字符串掩码
masked = StringUtils.mask_string("1234567890", start=6)  # 123456****
```

### 日期时间工具

```python
from core.utils.datetime import DateTimeUtils

# 获取当前时间戳
timestamp = DateTimeUtils.get_timestamp()

# 格式化日期时间
formatted = DateTimeUtils.format_datetime(datetime.now(), "YYYY-MM-DD HH:mm:ss")

# 时间计算
next_week = DateTimeUtils.add_days(datetime.now(), 7)
last_month = DateTimeUtils.add_months(datetime.now(), -1)

# 时区转换
utc_time = DateTimeUtils.to_utc(local_time)
local_time = DateTimeUtils.to_local(utc_time)
```

### 数据工具

```python
from core.utils.data import DataUtils

# 深拷贝
copied = DataUtils.deep_copy(original_data)

# 数据合并
merged = DataUtils.merge_dicts(dict1, dict2)

# 类型转换
int_value = DataUtils.safe_int("123", default=0)
float_value = DataUtils.safe_float("12.34", default=0.0)

# 数据验证
is_valid = DataUtils.validate_email("user@example.com")
is_valid = DataUtils.validate_phone("13800138000")
```

## 配置选项

```python
UTILS_CONFIG = {
    "string": {
        "default_encoding": "utf-8",
        "template_engine": "jinja2",
        "mask_char": "*"
    },
    "datetime": {
        "default_timezone": "UTC",
        "date_format": "YYYY-MM-DD",
        "datetime_format": "YYYY-MM-DD HH:mm:ss"
    },
    "security": {
        "hash_algorithm": "sha256",
        "salt_length": 16,
        "key_size": 32
    },
    "data": {
        "max_recursion_depth": 100,
        "default_encoding": "utf-8",
        "serializer": "json"
    }
}
```

## 最佳实践

1. 函数设计
   - 单一职责
   - 参数验证
   - 返回值明确
   - 异常处理

2. 性能优化
   - 缓存结果
   - 避免重复计算
   - 资源复用
   - 内存管理

3. 代码质量
   - 完整测试
   - 清晰文档
   - 代码示例
   - 性能基准

## 注意事项

1. 通用性
   - 适用范围
   - 兼容性
   - 扩展性
   - 可维护性

2. 安全性
   - 输入验证
   - 错误处理
   - 安全检查
   - 日志记录

3. 性能影响
   - 执行效率
   - 内存使用
   - 并发处理
   - 资源消耗 