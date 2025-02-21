import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request
from pydantic import BaseModel


class LogConfig(BaseModel):
    """日志配置"""

    LOGGER_NAME: str = "project_name"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "INFO"

    # 日志文件配置
    LOG_FILE: Optional[str] = None
    MAX_BYTES: int = 10_000_000  # 10MB
    BACKUP_COUNT: int = 5

    class Config:
        case_sensitive = True


class UnifiedLogger:
    """统一的日志记录器"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(name)
        self.config = LogConfig(**(config or {}))
        self._setup_logger()

    def _setup_logger(self) -> None:
        """配置日志记录器"""
        self.logger.setLevel(self.config.LOG_LEVEL)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(self.config.LOG_FORMAT))
        self.logger.addHandler(console_handler)

        # 文件处理器(如果配置了日志文件)
        if self.config.LOG_FILE:
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                self.config.LOG_FILE,
                maxBytes=self.config.MAX_BYTES,
                backupCount=self.config.BACKUP_COUNT,
            )
            file_handler.setFormatter(logging.Formatter(self.config.LOG_FORMAT))
            self.logger.addHandler(file_handler)

    def _get_base_log_data(self, request: Optional[Request] = None) -> Dict[str, Any]:
        """获取基础日志数据"""
        log_data = {"timestamp": datetime.now().isoformat(), "logger": self.logger.name}

        if request:
            log_data.update(
                {
                    "request_id": getattr(request.state, "request_id", None),
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                }
            )

        return log_data

    def log_request(self, request: Request, **kwargs) -> None:
        """记录请求日志"""
        log_data = self._get_base_log_data(request)
        log_data.update(kwargs)

        self.logger.info("Request started", extra=log_data)

    def log_response(self, request: Request, status_code: int, process_time: float, **kwargs) -> None:
        """记录响应日志"""
        log_data = self._get_base_log_data(request)
        log_data.update({"status_code": status_code, "process_time": process_time, **kwargs})

        self.logger.info("Request completed", extra=log_data)

    def log_error(self, request: Request, exc: Exception, **kwargs) -> None:
        """记录错误日志"""
        log_data = self._get_base_log_data(request)
        log_data.update(
            {
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
                **kwargs,
            }
        )

        self.logger.error("Error occurred", extra=log_data, exc_info=True)

    def info(self, msg: str, *args, **kwargs) -> None:
        """记录信息日志"""
        self.logger.info(
            msg,
            *args,
            **kwargs,
        )

    def error(self, msg: str, *args, **kwargs) -> None:
        """记录错误日志"""
        self.logger.error(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """记录警告日志"""
        self.logger.warning(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """记录调试日志"""
        self.logger.debug(msg, *args, **kwargs)
