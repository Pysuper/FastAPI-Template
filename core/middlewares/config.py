import json
from typing import Dict, Any

import yaml

from core.config.manager import ConfigManager


class MiddlewareConfigManager(ConfigManager):
    """中间件配置管理器"""

    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.middleware_configs: Dict[str, Dict[str, Any]] = {}

    def load_config(self) -> None:
        """加载中间件配置"""
        super().load_config()
        self.middleware_configs = self.config.get("middlewares", {})

    def get_middleware_config(self, name: str) -> Dict[str, Any]:
        """获取中间件配置"""
        return self.middleware_configs.get(name, {})

    def update_middleware_config(self, name: str, config: Dict[str, Any]) -> None:
        """更新中间件配置"""
        old_config = self.middleware_configs.get(name, {})
        self.middleware_configs[name] = config
        self._notify_change(f"middlewares.{name}", old_config, config)

        # 保存到文件
        self.config["middlewares"] = self.middleware_configs
        self._save_config()

    def _save_config(self) -> None:
        """保存配置到文件"""
        try:
            if self.config_path.suffix in (".yml", ".yaml"):
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(self.config, f)
            elif self.config_path.suffix == ".json":
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=2)

            self.logger.info("Config saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save config: {str(e)}")
            raise
