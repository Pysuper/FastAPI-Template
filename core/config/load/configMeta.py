# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：configMeta.py
@Author  ：PySuper
@Date    ：2024/12/31 14:20 
@Desc    ：Speedy configMeta.py
"""
from core.config.load.base import ConfigMetadata


class ConfigMeta(ConfigMetadata):
    """配置元数据"""

    name: str = "Speedy"
    version: str = "0.1.0"
    environment: str = "development"
    description: str = "Speedy Application Settings"
    author: str = "PySuper"
    contact: str = "admin@example.com"
    website: str = "https://project_name.io"
