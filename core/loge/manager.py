# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2025/1/2 17:59 
@Desc    ：Speedy manager.py
"""

import logging
from contextlib import contextmanager
from typing import Any, Optional

from core.loge.logger import CustomLogger, LogConfig


class LoggingManager:
    """日志管理器，用于管理应用程序的日志配置和记录"""

    def __init__(self):
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            from core.loge.logger import CustomLogger
            self._logger = CustomLogger("project_name")
        return self._logger

    async def init(self, config: Optional[LogConfig] = None) -> None:
        """初始化日志管理器"""
        if config:
            # 应用配置
            self._apply_config(config)
        print(" ✅ LoggingManager")

    async def close(self) -> None:
        """关闭日志管理器"""
        if self._logger is not None:
            for handler in self._logger.handlers[:]:
                self._logger.removeHandler(handler)
                if hasattr(handler, 'close'):
                    handler.close()

    def _setup_third_party_loggers(self) -> None:
        """配置第三方库的日志级别"""
        third_party_loggers = ["urllib3", "asyncio", "aiohttp", "sqlalchemy", "uvicorn"]
        for logger_name in third_party_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    def _apply_config(self, config: LogConfig) -> None:
        """应用日志配置"""
        self.logger.setLevel(getattr(logging, config.level.upper()))
        # 可以添加更多配置项的应用逻辑

    @contextmanager
    def log_context(self, **kwargs: Any) -> None:
        """日志上下文管理器，用于临时设置日志字段"""
        previous = {}
        try:
            # 保存当前值并设置新值
            for key, value in kwargs.items():
                filter_obj = self.logger.filters[0]
                previous[key] = getattr(filter_obj, key, None)
                setattr(filter_obj, key, value)
            yield
        finally:
            # 恢复之前的值
            for key, value in previous.items():
                setattr(self.logger.filters[0], key, value)

    def debug_with_extra(self, msg: str, extra_fields: Optional[dict] = None, **kwargs) -> None:
        """带额外字段的DEBUG级别日志"""
        self.logger.debug_with_extra(msg, extra_fields, **kwargs)

    def info_with_extra(self, msg: str, extra_fields: Optional[dict] = None, **kwargs) -> None:
        """带额外字段的INFO级别日志"""
        self.logger.info_with_extra(msg, extra_fields, **kwargs)

    def warning_with_extra(self, msg: str, extra_fields: Optional[dict] = None, **kwargs) -> None:
        """带额外字段的WARNING级别日志"""
        self.logger.warning_with_extra(msg, extra_fields, **kwargs)

    def error_with_extra(self, msg: str, extra_fields: Optional[dict] = None, **kwargs) -> None:
        """带额外字段的ERROR级别日志"""
        self.logger.error_with_extra(msg, extra_fields, **kwargs)

    def critical_with_extra(self, msg: str, extra_fields: Optional[dict] = None, **kwargs) -> None:
        """带额外字段的CRITICAL级别日志"""
        self.logger.critical_with_extra(msg, extra_fields, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """DEBUG级别日志"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """INFO级别日志"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """WARNING级别日志"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """ERROR级别日志"""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """CRITICAL级别日志"""
        self.logger.critical(msg, *args, **kwargs)


# 创建全局日志管理器实例
logic = LoggingManager()
