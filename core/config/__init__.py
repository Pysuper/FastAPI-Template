# # -*- coding:utf-8 -*-
# """
# @Project ：Speedy
# @File    ：__init__.py
# @Author  ：PySuper
# @Date    ：2024-12-19 23:14
# @Desc    ：Speedy __init__
# """
#
from pathlib import Path
from typing import Optional

from core.config.settings.registry import settings_registry
from core.config.load import *  # noqa: F401,F403
from core.config.load.base import BaseSettings

#
#
# def init_settings(config_dir: Optional[str] = None, env: str = "development") -> None:
#     """初始化所有配置"""
#
#     # 注册所有配置类
#     settings_registry.register(APIConfig)
#     settings_registry.register(AppConfig)
#     # settings_registry.register(CacheConfig)
#     settings_registry.register(CORSConfig)
#     settings_registry.register(DatabaseConfig)
#     settings_registry.register(EmailConfig)
#     settings_registry.register(FileConfig)
#     settings_registry.register(LogConfig)
#     settings_registry.register(RateLimiterConfig)
#     settings_registry.register(SecurityConfig)
#     settings_registry.register(ServiceConfig)
#
#     # 设置默认配置目录
#     if config_dir is None:
#         config_dir = str(Path(__file__).parent.parent.parent.parent / "config")
#
#     # 加载所有配置
#     settings_registry.load_all(config_dir, env)
#
#
# def get_settings(key: str) -> Optional[BaseSettings]:
#     """获取配置实例"""
#     return settings_registry.get(key)
