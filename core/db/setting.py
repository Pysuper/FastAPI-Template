# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：setting.py
@Author  ：PySuper
@Date    ：2025-01-02 20:14
@Desc    ：数据库配置管理模块
"""
from typing import Any, Dict

from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """数据库配置类"""

    # 数据库连接配置
    DB_DRIVER: str = Field(default="postgresql", description="数据库驱动")
    DB_HOST: str = Field(default="localhost", description="数据库主机")
    DB_PORT: int = Field(default=5432, description="数据库端口")
    DB_NAME: str = Field(..., description="数据库名称")
    DB_USER: str = Field(..., description="数据库用户名")
    DB_PASSWORD: str = Field(..., description="数据库密码")

    # 连接池配置
    POOL_SIZE: int = Field(default=5, description="连接池大小")
    POOL_TIMEOUT: int = Field(default=30, description="连接池超时时间(秒)")
    MAX_OVERFLOW: int = Field(default=10, description="最大溢出连接数")

    # 会话配置
    SESSION_TIMEOUT: int = Field(default=300, description="会话超时时间(秒)")

    # 重试配置
    RETRY_COUNT: int = Field(default=3, description="重试次数")
    RETRY_INTERVAL: int = Field(default=1, description="重试间隔(秒)")

    # 日志配置
    ENABLE_QUERY_LOGGING: bool = Field(default=False, description="是否启用SQL查询日志")
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")

    class Config:
        env_prefix = "DB_"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """获取数据库URL"""
        return f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def get_pool_settings(self) -> Dict[str, Any]:
        """获取连接池配置"""
        return {"pool_size": self.POOL_SIZE, "max_overflow": self.MAX_OVERFLOW, "pool_timeout": self.POOL_TIMEOUT}

    def get_retry_settings(self) -> Dict[str, Any]:
        """获取重试配置"""
        return {"retry_count": self.RETRY_COUNT, "retry_interval": self.RETRY_INTERVAL}


# 全局配置实例
db_settings = DatabaseSettings()
