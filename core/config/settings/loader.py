import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Type

import yaml

from core.config.load.base import BaseConfig, BaseSettings

logger = logging.getLogger(__name__)


class BaseLoader(ABC):
    """配置加载器基类"""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """加载配置"""
        pass


class EnvConfigLoader(BaseLoader):
    """环境变量配置加载器"""

    def __init__(self, prefix: str = "APP_"):
        self.prefix = prefix

    def load(self) -> Dict[str, Any]:
        config = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config[key[len(self.prefix) :].lower()] = value
        return config


class JsonConfigLoader(BaseLoader):
    """JSON文件配置加载器"""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            return {}

        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)


class YamlConfigLoader(BaseLoader):
    """YAML文件配置加载器"""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            return {}

        with open(self.file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


class ConfigLoader:
    """
    配置加载器模块
    用于从不同来源（文件、环境变量等）加载配置
    """

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.env_prefix = "SPEEDY_"

    def load_from_file(self, file_path: Path) -> Dict[str, Any]:
        """从YAML文件加载配置"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"加载配置文件失败 {file_path}: {e}")
            return {}

    def load_from_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """从环境变量加载配置"""
        result = config.copy()

        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                config_key = key[len(self.env_prefix) :].lower()
                self._set_nested_value(result, config_key.split("_"), value)

        return result

    def _set_nested_value(self, config: Dict[str, Any], keys: list[str], value: Any) -> None:
        """设置嵌套的配置值"""
        current = config
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value

    def load_config(self, name: str) -> Dict[str, Any]:
        """
        加载指定名称的配置
        :param name: 配置文件名称
        :return: 配置数据字典
        """
        # 加载基础配置文件
        config_file = self.config_dir / name
        config_data = self.load_from_file(config_file)

        # 加载环境特定的配置文件
        env = os.getenv("ENV", "dev")
        env_config_file = config_file.parent / f"{config_file.stem}.{env}{config_file.suffix}"
        if env_config_file.exists():
            env_config_data = self.load_from_file(env_config_file)
            config_data.update(env_config_data)

        # 应用环境变量覆盖
        config_data = self.load_from_env(config_data)

        return config_data

    def validate_config(self, config: BaseConfig) -> bool:
        """验证配置是否有效"""
        try:
            config.model_validate(config.model_dump())
            return True
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False

    async def load_all(self):
        """加载所有配置"""
        # 获取所有配置类
        config_classes = self._get_config_classes()

        # 并发加载所有配置
        tasks = []
        for name, config_class in config_classes.items():
            task = asyncio.create_task(self._load_config_async(name, config_class))
            tasks.append(task)

        # 等待所有配置加载完成
        configs = await asyncio.gather(*tasks)

        # 验证配置
        for config in configs:
            if config and not self.validate_config(config):
                logger.error(f"配置验证失败: {config.__class__.__name__}")

        return {config.__class__.__name__: config for config in configs if config}

    def _get_config_classes(self):
        """获取所有配置类"""
        config_classes = {}
        # 扫描配置目录下的所有yaml文件
        for file in self.config_dir.glob("*.yaml"):
            # 忽略环境特定的配置文件
            if "." in file.stem:
                continue
            name = file.stem
            # 获取对应的配置类
            config_class = self.get_config_class(name)
            if config_class:
                config_classes[name] = config_class
        return config_classes

    async def _load_config_async(self, name, config_class):
        """异步加载单个配置"""
        try:
            # 加载基础配置文件
            config_file = self.config_dir / f"{name}.yaml"
            config_data = self.load_from_file(config_file)

            # 加载环境特定的配置
            env = os.getenv("ENV", "dev")
            env_config_file = self.config_dir / f"{name}.{env}.yaml"
            if env_config_file.exists():
                env_config_data = self.load_from_file(env_config_file)
                config_data.update(env_config_data)

            # 应用环境变量覆盖
            config_data = self.load_from_env(config_data)

            # 创建并返回配置实例
            return config_class(**config_data)
        except Exception as e:
            logger.error(f"加载配置失败 {name}: {e}")
            return None

    def get_config_class(self, name):
        """获取配置类

        Args:
            name: 配置名称

        Returns:
            配置类或None
        """
        try:
            # 尝试从custom.config.settings模块导入配置类
            module_name = f"custom.config.settings.{name}"
            module = __import__(module_name, fromlist=["*"])

            # 获取配置类名称
            class_name = "".join(word.capitalize() for word in name.split("_")) + "Config"

            # 从模块中获取配置类
            if hasattr(module, class_name):
                config_class = getattr(module, class_name)
                # 验证是否是BaseConfig的子类
                if isinstance(config_class, type) and issubclass(config_class, BaseConfig):
                    return config_class

            logger.warning(f"未找到配置类: {class_name}")
            return None

        except ImportError:
            logger.warning(f"未找到配置模块: {name}")
            return None
        except Exception as e:
            logger.error(f"获取配置类失败 {name}: {e}")
            return None


class SettingsLoader:
    """配置加载器"""

    def __init__(self):
        self._settings_classes: Dict[str, Type[BaseSettings]] = {}
        self._settings_instances: Dict[str, BaseSettings] = {}

    def register(self, settings_class: Type[BaseSettings]) -> None:
        """注册配置类"""
        key = settings_class.get_settings_key()
        self._settings_classes[key] = settings_class

    def load_all(self, config_dir: Path, env: str = "development") -> None:
        """加载所有配置"""
        # 加载配置文件
        config_data = self._load_config_files(config_dir, env)

        # 加载环境变量
        env_config = self._load_environment_variables()

        # 合并配置
        merged_config = self._merge_configs(config_data, env_config)

        # 创建配置实例
        self._create_settings_instances(merged_config, env)

    def get(self, key: str) -> BaseSettings:
        """获取配置实例"""
        return self._settings_instances.get(key)

    def _load_config_files(self, config_dir: Path, env: str) -> Dict[str, Any]:
        """加载配置文件"""
        config_data = {}

        # 加载基础配置
        base_config = self._load_yaml_file(config_dir / "config.yaml")
        config_data.update(base_config)

        # 加载环境特定配置
        env_config_file = config_dir / f"config.{env}.yaml"
        if env_config_file.exists():
            env_config = self._load_yaml_file(env_config_file)
            config_data = self._deep_merge(config_data, env_config)

        return config_data

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """加载YAML文件"""
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _load_environment_variables(self) -> Dict[str, Any]:
        """加载环境变量"""
        config = {}
        prefix = "SPEEDY_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix) :].lower().split("_")
                current = config
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = value

        return config

    def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """合并多个配置"""
        result = {}
        for config in configs:
            result = self._deep_merge(result, config)
        return result

    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _create_settings_instances(self, config: Dict[str, Any], env: str) -> None:
        """创建配置实例"""
        for key, settings_class in self._settings_classes.items():
            settings_data = config.get(key, {})
            settings_data["metadata"] = {"environment": env, "name": key}
            self._settings_instances[key] = settings_class(**settings_data)
