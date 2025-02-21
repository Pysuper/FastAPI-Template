# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：Speedy manager
"""
import asyncio
import logging
from typing import Dict

from cache.config.config import RedisConfig
from core.config.setting import settings


class ConfigManager:
    """配置管理中心"""

    _instance = None

    def __new__(cls):
        """
        使用单例模式确保全局只有一个配置管理实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._logger = logging.getLogger(__name__)
        self._managers: Dict[str, object] = {}
        self._initialized = False
        self._logger.info("Configuration manager initialized successfully")

    def _get_manager(self, name: str) -> object:
        """懒加载获取管理器"""
        if name not in self._managers:
            # 定义管理器映射关系
            manager_mapping = {
                "cache": ("core.cache.manager", "CacheManager", RedisConfig),
                "database": ("core.db.core.manager", "DatabaseManager", settings.db),
                "logger": ("core.loge.logger", "LogManager", None),
                "middleware": ("core.middlewares.manager", "MiddlewareManager", settings.middleware),
                "model": ("models.manager", "ModelManager", None),
                "response": ("core.response.manager", "ResponseManager", None),
                "schema": ("schemas.manager", "SchemaManager", None),
                "security": ("core.security.manager", "SecurityManager", None),
                "audit": ("core.audit.manager", "AuditManager", None),
                "service": ("core.services.manager", "ServiceManager", None),
                "task": ("core.tasks.manager", "TaskManager", None),
                "util": ("core.utils.manager", "UtilManager", None),
                "strong": ("core.strong.manager", "StrongManager", None),
            }

            if name not in manager_mapping:
                raise ValueError(f"未知的管理器类型: {name}")

            manager_info = manager_mapping[name]

            # 如果是已导入的类,直接实例化
            if isinstance(manager_info[0], type):
                manager_class = manager_info[0]
            else:
                # 动态导入管理器类
                module = __import__(manager_info[0], fromlist=[manager_info[1]])
                manager_class = getattr(module, manager_info[1])

            # 根据是否有初始化参数创建实例
            if manager_info[2] is not None:
                self._managers[name] = manager_class(manager_info[2])
            else:
                self._managers[name] = manager_class()

        return self._managers[name]

    @property
    def cache(self):
        """获取缓存管理器"""
        return self._get_manager("cache")

    @property
    def database(self):
        return self._get_manager("database")

    @property
    def logger(self):
        return self._get_manager("logger")

    @property
    def middleware(self):
        return self._get_manager("middleware")

    @property
    def model(self):
        return self._get_manager("model")

    @property
    def response(self):
        return self._get_manager("response")

    @property
    def schema(self):
        return self._get_manager("schema")

    @property
    def security(self):
        return self._get_manager("security")

    @property
    def service(self):
        return self._get_manager("service")

    @property
    def task(self):
        return self._get_manager("task")

    @property
    def util(self):
        return self._get_manager("util")

    @property
    def strong(self):
        return self._get_manager("strong")

    async def init(self):
        """初始化所有组件"""
        if self._initialized:
            return

        try:
            # 初始化各个管理器
            await self.cache.init(settings.cache)
            await self.database.init(settings.db)
            await self.logger.init(settings.log)
            await self.middleware.init(settings.middleware)
            await self.security.init(settings.security)
            await self.service.init(settings.service)
            await self.task.init(settings.task)

            # 启动配置监控
            self._start_config_watching()

            self._initialized = True
            self._logger.info("Configuration manager initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize configuration manager: {e}")
            raise

    async def close(self):
        """关闭所有组件"""
        try:
            # 停止配置监控
            settings._watcher.stop()

            # 关闭各个管理器
            for manager in self._managers.values():
                await manager.close()

            # 清理管理器
            self._managers.clear()

            self._initialized = False
            self._logger.info("Configuration manager closed successfully")
        except Exception as e:
            self._logger.error(f"Failed to close configuration manager: {e}")
            raise

    def _start_config_watching(self):
        """启动配置监控"""

        def on_config_change():
            """配置变更处理"""
            self._logger.info("Configuration changed, reloading...")
            asyncio.create_task(self.reload())

        settings._watcher.start("config", on_config_change)

    async def reload(self):
        """重新加载配置"""
        try:
            # 更新各个管理器
            for name, manager in self._managers.items():
                config = settings.get_config(name)
                await manager.reload(config)

            self._logger.info("Configuration reloaded successfully")
        except Exception as e:
            self._logger.error(f"Failed to reload configuration: {e}")
            raise


# 创建全局配置管理器实例
config_manager = ConfigManager()
