"""
安全配置模块

提供安全相关的配置项
"""
from typing import List, Optional
from pydantic import BaseModel


class SecurityConfig(BaseModel):
    """安全配置模型"""

    # 基础配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"

    # Token配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 密码策略
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPER: bool = True
    PASSWORD_REQUIRE_LOWER: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # 加密配置
    ENCRYPTION_KEY: Optional[str] = None
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"

    # 会话配置
    SESSION_COOKIE_NAME: str = "session"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"

    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_WINDOW: int = 60

    # 审计配置
    AUDIT_ENABLED: bool = True
    AUDIT_LOG_PATH: str = "logs/audit.log"

    # SQL注入防护配置
    SQL_INJECTION_PROTECTION: bool = True
    SQL_INJECTION_LOG: bool = True

    # RBAC配置
    RBAC_ENABLED: bool = True
    RBAC_CACHE_TTL: int = 300  # 5分钟

    class Config:
        """Pydantic配置"""

        case_sensitive = True
