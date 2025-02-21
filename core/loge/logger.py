"""
日志模块

提供统一的日志记录功能，包含以下特性：
    1. JSON格式输出
    2. 控制台和文件双重输出
    3. 日志文件自动轮转
    4. 支持额外字段记录
    5. 支持请求追踪
    6. 支持上下文管理
"""

import json
import logging
import platform
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler, WatchedFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel

# 根据系统类型导入不同的锁机制
SYSTEM_TYPE = platform.system().lower()
if SYSTEM_TYPE == "windows":
    pass
else:
    import fcntl

# 为每个日志文件创建一个锁
file_locks = {}
lock_creation_lock = threading.Lock()


def get_log_level(level: Union[str, int]) -> int:
    """转换日志级别为整数值"""
    if isinstance(level, int):
        return level

    # 如果是枚举值，获取其字符串表示
    if hasattr(level, "value"):
        level = level.value

    # 将字符串转换为大写
    level_upper = str(level).upper()

    # 获取日志级别
    level_mapping = {
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.FATAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "WARN": logging.WARN,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }

    return level_mapping.get(level_upper, logging.INFO)


class LogConfig(BaseModel):
    """日志配置模型"""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_dir: str = "logs"
    json_format: bool = True
    console_output: bool = True
    file_output: bool = True
    error_file_output: bool = True


class ProcessSafeHandler(WatchedFileHandler):
    """进程安全的日志处理器"""

    def __init__(self, filename, mode="a", encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        # 为每个文件创建一个锁
        with lock_creation_lock:
            if filename not in file_locks:
                file_locks[filename] = threading.Lock()
        self.file_lock = file_locks[filename]

    def emit(self, record):
        """确保多进程写入安全"""
        try:
            if SYSTEM_TYPE == "windows":
                self._windows_safe_emit(record)
            else:
                self._unix_safe_emit(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

    def _windows_safe_emit(self, record):
        """Windows系统的安全写入实现"""
        with self.file_lock:
            try:
                super().emit(record)
            except Exception:
                self.handleError(record)

    def _unix_safe_emit(self, record):
        """Unix/Linux系统的安全写入实现"""
        # 获取文件描述符
        fd = self.stream.fileno()
        # 加文件锁
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            super().emit(record)
        finally:
            # 释放文件锁
            fcntl.flock(fd, fcntl.LOCK_UN)


class BaseFormatter(logging.Formatter):
    """基础日志格式化器"""

    def __init__(self) -> None:
        super().__init__()
        self.default_fields = [
            "timestamp",
            "level",
            "message",
            "module",
            "function",
            "line",
        ]

    def get_basic_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """获取基础字段"""
        return {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }


class JsonFormatter(BaseFormatter):
    """JSON格式的日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON格式"""
        log_data = self.get_basic_fields(record)

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # 添加请求ID和追踪ID
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id

        # 添加进程和线程信息
        log_data["process"] = {"id": record.process, "name": record.processName}
        log_data["thread"] = {"id": record.thread, "name": record.threadName}

        return json.dumps(log_data, ensure_ascii=False)


class CustomLogger:
    """增强的日志记录器，支持额外字段和JSON格式化"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self._initialized = False

    @property
    def handlers(self):
        """获取所有处理器"""
        return self.logger.handlers

    def addHandler(self, handler):
        """添加处理器"""
        self.logger.addHandler(handler)

    def removeHandler(self, handler):
        """移除处理器"""
        self.logger.removeHandler(handler)

    def _setup_handlers(self):
        if self._initialized:
            return

        from core.config.setting import settings

        log_dir = Path(settings.log.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 设置日志格式
        formatter = logging.Formatter(fmt=settings.log.BASE_LOG_FORMAT, datefmt=settings.log.DATE_FORMAT)

        # 控制台处理器
        if settings.log.CONSOLE_OUTPUT:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(get_log_level(settings.log.CONSOLE_LEVEL))
            self.logger.addHandler(console_handler)

        # 文件处理器
        if settings.log.FILE_OUTPUT:
            file_handler = RotatingFileHandler(
                filename=str(log_dir / "app.log"),
                maxBytes=settings.log.MAX_BYTES,
                backupCount=settings.log.BACKUP_COUNT,
                encoding=settings.log.ENCODING,
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(get_log_level(settings.log.FILE_LEVEL))
            self.logger.addHandler(file_handler)

        self.logger.setLevel(get_log_level(settings.log.LEVEL))
        self._initialized = True

    def _ensure_initialized(self):
        if not self._initialized:
            self._setup_handlers()

    def debug(self, msg, *args, **kwargs):
        self._ensure_initialized()
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._ensure_initialized()
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._ensure_initialized()
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._ensure_initialized()
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._ensure_initialized()
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        self._ensure_initialized()
        self.logger.exception(msg, *args, exc_info=exc_info, **kwargs)


class RequestIdFilter(logging.Filter):
    """请求ID过滤器，用于在日志记录中添加请求ID和追踪ID"""

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self.request_id: Optional[str] = None
        self.trace_id: Optional[str] = None

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录，添加请求ID和追踪ID"""
        record.request_id = getattr(record, "request_id", self.request_id)
        record.trace_id = getattr(record, "trace_id", self.trace_id)
        return True


# 导出
__all__ = [
    "LogConfig",
    "CustomLogger",
    "RequestIdFilter",
]
