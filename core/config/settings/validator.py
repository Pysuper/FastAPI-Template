from typing import Any, List

from pydantic import ValidationError

from core.config.load.base import BaseConfig


class ConfigValidator:
    """配置验证器"""

    def validate_config(self, config: BaseConfig) -> bool:
        """
        验证配置
        :param config: 配置实例
        :return: 是否验证通过
        """
        try:
            # 验证配置模型
            config.model_validate(config.model_dump())
            return True
        except ValidationError as e:
            print(f"配置验证失败: {e}")
            return False

    def validate_env_vars(self, required_vars: List[str]) -> List[str]:
        """
        验证必需的环境变量
        :param required_vars: 必需的环境变量列表
        :return: 缺失的环境变量列表
        """
        import os

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        return missing_vars
