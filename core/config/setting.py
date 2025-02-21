"""
@Project ：Speedy 
@File    ：setting.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：Speedy setting
"""

from functools import lru_cache

from core.config.load.sms import SMSConfig
from core.cache.config.config import CacheConfig
from core.config import *  # noqa
from core.config.load.configMeta import ConfigMeta
from core.config.load.i18n import I18NConfig
from core.config.load.log import LogConfig
from core.middlewares.base import MiddlewareConfig
from security.audit.config import AuditConfig
from tasks.config import TaskConfig


class Settings(BaseSettings):
    """应用配置"""

    metadata: ConfigMeta = ConfigMeta()
    api: APIConfig = APIConfig()
    app: AppConfig = AppConfig()
    cache: CacheConfig = CacheConfig()  # 这是缓存配置（不只是Redis）
    cors: CORSConfig = CORSConfig()
    db: DatabaseConfig = DatabaseConfig()
    email: EmailConfig = EmailConfig()
    sms: SMSConfig = SMSConfig()
    file: FileConfig = FileConfig()
    log: LogConfig = LogConfig()
    audit: AuditConfig = AuditConfig()
    middleware: MiddlewareConfig = MiddlewareConfig()
    rate_limiter: RateLimiterConfig = RateLimiterConfig()
    security: SecurityConfig = SecurityConfig()
    i18n: I18NConfig = I18NConfig()
    service: ServiceConfig = ServiceConfig()
    task: TaskConfig = TaskConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


@lru_cache()
def get_settings() -> Settings:
    """获取配置"""
    return Settings()


settings = get_settings()
