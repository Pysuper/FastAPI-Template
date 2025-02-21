# 常量模块

## 模块简介

常量模块提供了应用程序中使用的各种常量定义，包括系统常量、业务常量、错误码、配置常量等。通过统一的常量管理，提高代码的可维护性和一致性。

## 核心功能

1. 系统常量
   - 环境常量
   - 路径常量
   - 时间常量
   - 编码常量
   - 限制常量

2. 业务常量
   - 状态码
   - 业务类型
   - 枚举值
   - 配置项
   - 默认值

3. 错误常量
   - 错误码
   - 错误消息
   - 异常类型
   - 验证规则
   - 响应码

4. 安全常量
   - 权限码
   - 加密类型
   - 安全配置
   - 令牌类型
   - 策略常量

## 使用方法

### 系统常量

```python
from core.constants import SystemConstants

# 环境常量
ENV_DEVELOPMENT = SystemConstants.ENV_DEVELOPMENT
ENV_PRODUCTION = SystemConstants.ENV_PRODUCTION
ENV_TESTING = SystemConstants.ENV_TESTING

# 时间常量
SECONDS_PER_DAY = SystemConstants.SECONDS_PER_DAY
SECONDS_PER_HOUR = SystemConstants.SECONDS_PER_HOUR
DEFAULT_TIMEOUT = SystemConstants.DEFAULT_TIMEOUT

# 路径常量
BASE_DIR = SystemConstants.BASE_DIR
CONFIG_DIR = SystemConstants.CONFIG_DIR
STATIC_DIR = SystemConstants.STATIC_DIR
```

### 业务常量

```python
from core.constants import BusinessConstants

# 用户状态
class UserStatus:
    ACTIVE = BusinessConstants.USER_STATUS_ACTIVE
    INACTIVE = BusinessConstants.USER_STATUS_INACTIVE
    BLOCKED = BusinessConstants.USER_STATUS_BLOCKED

# 订单类型
class OrderType:
    NORMAL = BusinessConstants.ORDER_TYPE_NORMAL
    EXPRESS = BusinessConstants.ORDER_TYPE_EXPRESS
    SPECIAL = BusinessConstants.ORDER_TYPE_SPECIAL
```

### 错误常量

```python
from core.constants import ErrorConstants

# 错误码
class ErrorCode:
    SUCCESS = ErrorConstants.SUCCESS
    INVALID_PARAMS = ErrorConstants.INVALID_PARAMS
    UNAUTHORIZED = ErrorConstants.UNAUTHORIZED
    FORBIDDEN = ErrorConstants.FORBIDDEN
    NOT_FOUND = ErrorConstants.NOT_FOUND
    SERVER_ERROR = ErrorConstants.SERVER_ERROR

# 错误消息
class ErrorMessage:
    INVALID_TOKEN = ErrorConstants.MSG_INVALID_TOKEN
    PERMISSION_DENIED = ErrorConstants.MSG_PERMISSION_DENIED
    RESOURCE_NOT_FOUND = ErrorConstants.MSG_RESOURCE_NOT_FOUND
```

## 配置选项

```python
CONSTANTS_CONFIG = {
    "system": {
        "environment": {
            "development": "development",
            "production": "production",
            "testing": "testing"
        },
        "encoding": {
            "default": "utf-8",
            "ascii": "ascii",
            "unicode": "unicode"
        },
        "timeout": {
            "default": 30,
            "short": 5,
            "long": 300
        }
    },
    "business": {
        "status": {
            "enabled": 1,
            "disabled": 0,
            "deleted": -1
        },
        "limits": {
            "max_retry": 3,
            "max_connections": 100,
            "max_size": 10485760
        }
    },
    "security": {
        "token": {
            "access": "access_token",
            "refresh": "refresh_token"
        },
        "encryption": {
            "algorithm": "HS256",
            "key_size": 2048
        }
    }
}
```

## 最佳实践

1. 命名规范
   - 全大写命名
   - 下划线分隔
   - 模块化组织
   - 清晰含义

2. 文档管理
   - 详细注释
   - 使用示例
   - 版本记录
   - 变更说明

3. 维护更新
   - 定期审查
   - 及时更新
   - 向后兼容
   - 废弃标记

## 注意事项

1. 设计原则
   - 单一职责
   - 避免重复
   - 语义明确
   - 易于维护

2. 使用规范
   - 统一引用
   - 避免硬编码
   - 类型提示
   - 版本控制

3. 安全考虑
   - 敏感信息
   - 访问控制
   - 加密存储
   - 更新机制 