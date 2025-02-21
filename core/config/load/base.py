# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：base.py
@Author  ：PySuper
@Date    ：2024/12/24 14:53 
@Desc    ：Speedy base.py
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class BaseConfig(BaseModel):
    """
    基础配置类
    """

    # 应用配置
    debug: bool = False
    env: str = "development"

    # 服务器配置
    host: str = "127.0.0.1"
    port: int = 8000

    # 日志配置
    log_level: str = "INFO"
    log_dir: Path = Path("logs")

    # 安全配置
    secret_key: str = Field(default="your-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # 数据库配置
    database_url: str = Field(default="sqlite:///./app.db", description="数据库连接URL")

    # Redis配置
    redis_url: str = Field(default="redis://localhost:your_port/0", description="Redis连接URL")

    # 缓存配置
    cache_type: str = "redis"  # redis 或 memory
    cache_prefix: str = "project_name:"
    cache_default_timeout: int = 300

    # CORS配置
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # 中间件配置
    middleware_configs: Dict[str, Any] = {
        "cors": {"enabled": True},
        "compression": {"enabled": True},
        "authentication": {"enabled": True},
        "rate_limit": {"enabled": True},
    }

    def __init__(self, _env_prefix: str = "", **kwargs):
        """
        初始化配置
        :param _env_prefix: 环境变量前缀
        """
        super().__init__(**kwargs)
        self._env_prefix = _env_prefix

    class Config:
        """Pydantic配置"""

        from_attributes = True
        validate_assignment = True
        arbitrary_types_allowed = True
        extra = "allow"
        json_schema_extra = {
            "example": {
                "debug": False,
                "env": "development",
                "host": "127.0.0.1",
                "port": 8000,
            }
        }

    def get_middleware_config(self, name: str) -> Dict[str, Any]:
        """获取中间件配置"""
        return self.middleware_configs.get(name, {"enabled": False})

    def update_middleware_config(self, name: str, config: Dict[str, Any]) -> None:
        """更新中间件配置"""
        if name in self.middleware_configs:
            self.middleware_configs[name].update(config)
        else:
            self.middleware_configs[name] = config

    async def init(self) -> None:
        """初始化配置，子类可以重写此方法以添加自定义初始化逻辑"""
        pass

    async def close(self) -> None:
        """关闭配置，子类可以重写此方法以添加自定义清理逻辑"""
        pass


class ConfigMetadata(BaseModel):
    """配置元数据"""

    name: str
    version: str
    environment: str
    description: Optional[str]
    author: Optional[str]
    contact: Optional[str]
    website: Optional[str]

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True
        extra = "allow"
        json_encoders = {datetime: lambda v: v.isoformat()}


class BaseSettings(BaseModel):
    """配置基类"""

    metadata: ConfigMetadata

    class Config:
        validate_assignment = True
        extra = "allow"
        json_encoders = {datetime: lambda v: v.isoformat()}

    @validator("metadata", pre=True, always=True)
    def set_metadata(cls, v):
        if isinstance(v, dict):
            v["name"] = cls.__name__
            return ConfigMetadata(**v)
        return v

    def update(self, data: Dict[str, Any]) -> None:
        """更新配置"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.metadata.updated_at = datetime.now()

    @classmethod
    def get_settings_key(cls) -> str:
        """获取配置键名"""
        return cls.__name__.lower().replace("settings", "")

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """转换为字典"""
        exclude_none = kwargs.pop("exclude_none", True)
        return super().dict(*args, exclude_none=exclude_none, **kwargs)
