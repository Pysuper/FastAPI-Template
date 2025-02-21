# 日志管理模块

## 模块简介

日志管理模块提供了统一的日志记录接口，支持多种日志输出方式，包括控制台、文件、远程服务等。支持日志分级、格式化、过滤和轮转等特性。

## 核心功能

1. 日志级别管理
   - DEBUG
   - INFO
   - WARNING
   - ERROR
   - CRITICAL

2. 日志输出方式
   - 控制台输出
   - 文件输出
   - JSON 格式输出
   - 远程日志服务

3. 日志特性
   - 日志轮转
   - 日志压缩
   - 日志过滤
   - 上下文追踪
   - 性能监控

## 使用方法

### 基础日志记录

```python
from core.loge import logger

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 带上下文的日志
logger.info("用户登录", extra={"user_id": 123, "ip": "127.0.0.1"})
```

### 日志上下文管理

```python
from core.loge import LogContext

with LogContext(request_id="abc123", user_id=456):
    logger.info("处理请求")  # 自动带上上下文信息
```

## 配置选项

```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "class": "core.loge.formatters.JsonFormatter",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
```

## 最佳实践

1. 日志级别使用
   - DEBUG: 开发调试信息
   - INFO: 正常业务流程
   - WARNING: 潜在问题警告
   - ERROR: 异常错误信息
   - CRITICAL: 严重系统错误

2. 日志内容规范
   - 包含必要的上下文信息
   - 使用结构化的日志格式
   - 避免记录敏感信息
   - 保持日志信息简洁明了

3. 日志管理
   - 定期归档和清理
   - 监控日志大小
   - 设置合适的轮转策略
   - 实现日志分析和告警

## 注意事项

1. 性能考虑
   - 避免过多的日志输出
   - 使用异步日志记录
   - 合理设置日志级别
   - 控制日志文件大小

2. 安全性
   - 脱敏敏感信息
   - 控制日志访问权限
   - 加密重要日志信息

3. 运维管理
   - 监控日志空间使用
   - 配置日志轮转策略
   - 实现日志备份机制
   - 建立日志分析系统 