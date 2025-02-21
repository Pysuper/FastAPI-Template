"""
配置注册器模块
用于管理所有模块的配置类的注册和加载
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Type

import yaml

from core.config.settings.loader import SettingsLoader
from core.config.load.base import BaseConfig, BaseSettings

logger = logging.getLogger(__name__)


class ConfigRegistry:
    """
    配置注册器
    管理所有模块的配置类
    """

    def __init__(self):
        self._registry: Dict[str, Type[BaseConfig]] = {}
        self._instances: Dict[str, BaseConfig] = {}

    def register(self, name: str, config_class: Type[BaseConfig]) -> None:
        """
        注册一个配置类
        :param name: 配置名称
        :param config_class: 配置类
        """
        if name in self._registry:
            logger.warning(f"配置 {name} 已存在，将被覆盖")
        self._registry[name] = config_class
        logger.info(f"注册配置类: {name}")

    def get_config_class(self, name: str) -> Optional[Type[BaseConfig]]:
        """获取配置类"""
        return self._registry.get(name)

    def get_instance(self, name: str) -> Optional[BaseConfig]:
        """获取配置实例"""
        return self._instances.get(name)

    def create_instance(self, name: str, **kwargs) -> Optional[BaseConfig]:
        """创建配置实例"""
        config_class = self.get_config_class(name)
        if not config_class:
            logger.error(f"配置类 {name} 不存在")
            return None

        instance = config_class(**kwargs)
        self._instances[name] = instance
        return instance

    def load_all_configs(self, config_dir: Path) -> None:
        """
        加载所有已注册的配置
        :param config_dir: 配置文件目录
        """
        for name, config_class in self._registry.items():
            config_file = config_dir / f"{name}.yaml"
            if config_file.exists():
                try:
                    # 从YAML文件加载配置
                    with open(config_file, "r", encoding="utf-8") as f:
                        config_data = yaml.safe_load(f) or {}

                    # 创建配置实例
                    instance = self.create_instance(name, **config_data)
                    if instance:
                        logger.info(f"从文件加载配置: {name}")
                    else:
                        logger.error(f"创建配置实例失败: {name}")
                except Exception as e:
                    logger.error(f"加载配置文件失败 {config_file}: {e}")
            else:
                logger.warning(f"配置文件不存在: {config_file}")

    async def init_all(self) -> None:
        """初始化所有配置实例"""
        for name, instance in self._instances.items():
            if hasattr(instance, "init"):
                await instance.init()

    async def close_all(self) -> None:
        """关闭所有配置实例"""
        for name, instance in self._instances.items():
            if hasattr(instance, "close"):
                await instance.close()


class SettingsRegistry:
    """配置注册器"""

    def __init__(self):
        self.loader = SettingsLoader()

    def register(self, settings_class: Type[BaseSettings]) -> None:
        """注册配置类"""
        self.loader.register(settings_class)

    def load_all(self, config_dir: str, env: str = "development") -> None:
        """加载所有配置"""
        self.loader.load_all(config_dir, env)

    def get(self, key: str) -> BaseSettings:
        """获取配置实例"""
        return self.loader.get(key)


# 全局配置注册器实例
config_registry = ConfigRegistry()

# 创建全局配置注册器实例
settings_registry = SettingsRegistry()
