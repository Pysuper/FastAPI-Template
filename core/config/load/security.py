"""
@Project ：Speedy
@File    ：setting.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：配置管理模块

提供应用配置的管理功能，包括：
    - 基础配置
    - 数据库配置
    - 安全配置
    - 缓存配置
    - 日志配置
    - 中间件配置
"""

from typing import List, Optional, Set

from pydantic import BaseModel, Field


class SecurityConfig(BaseModel):
    """安全配置"""

    SENSITIVE_FIELDS: Set[str] = Field(default={"password", "token", "secret", "key"}, description="敏感字段集合")
    ENCRYPTION_EXCLUDE_PATHS: Set[str] = Field(default={"/docs", "/redoc", "/openapi.json"}, description="加密排除路径")
    AUTH_EXCLUDE_PATHS: Set[str] = Field(
        default={"/docs", "/redoc", "/openapi.json", "/api/v1/auth/login"}, description="认证排除路径"
    )

    # 密钥配置
    SECRET_KEY: str = Field(default="your-secret-key", description="密钥")
    ALGORITHM: str = Field(default="HS256", description="加密算法")

    # Token配置
    AUTH_TOKEN_HEADER: str = Field(default="Authorization", description="认证令牌头")
    AUTH_TOKEN_PREFIX: str = Field(default="Bearer", description="认证令牌前缀")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, description="刷新令牌过期时间(分钟)")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="刷新令牌过期时间")

    # 密码策略
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="密码最小长度")
    PASSWORD_REQUIRE_UPPER: bool = Field(default=True, description="密码需要大写字母")
    PASSWORD_REQUIRE_LOWER: bool = Field(default=True, description="密码需要小写字母")
    PASSWORD_REQUIRE_DIGIT: bool = Field(default=True, description="密码需要数字")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, description="密码需要特殊字符")

    # 限流配置
    ENABLE_RATE_LIMIT: bool = Field(default=True, description="是否启用限流")
    RATE_LIMIT_STRATEGY: str = Field(default="fixed-window", description="限流策略")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="限流请求数")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="限流窗口")

    # IP白名单
    ENABLE_IP_WHITELIST: bool = Field(default=False, description="是否启用IP白名单")
    IP_WHITELIST: List[str] = Field(default=["127.0.0.1"], description="IP白名单列表")

    # CORS配置
    CORS_ENABLED: bool = Field(default=True, description="是否启用CORS")
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS允许的源")
    CORS_METHODS: List[str] = Field(default=["*"], description="CORS允许的方法")
    CORS_HEADERS: List[str] = Field(default=["*"], description="CORS允许的头部")

    # SSL/TLS配置
    SSL_ENABLED: bool = Field(default=False, description="是否启用SSL")
    SSL_CERT_FILE: Optional[str] = Field(default=None, description="SSL证书文件")
    SSL_KEY_FILE: Optional[str] = Field(default=None, description="SSL密钥文件")

    # 会话配置
    SESSION_ENABLED: bool = Field(default=True, description="是否启用会话")
    SESSION_SECRET: str = Field(default="your-session-secret", description="会话密钥")
    SESSION_EXPIRE: int = Field(default=86400, description="会话过期时间")

    # CSRF配置
    CSRF_ENABLED: bool = Field(default=True, description="是否启用CSRF")
    CSRF_SECRET: str = Field(default="your-csrf-secret", description="CSRF密钥")
    CSRF_METHODS: List[str] = Field(default=["POST", "PUT", "DELETE", "PATCH"], description="CSRF保护的方法")

    # 安全头部
    SECURITY_HEADERS_ENABLED: bool = Field(default=True, description="是否启用安全头部")
    HSTS_ENABLED: bool = Field(default=False, description="是否启用HSTS")
    FRAME_DENY: bool = Field(default=True, description="是否禁止iframe嵌入")
    CONTENT_TYPE_NOSNIFF: bool = Field(default=True, description="是否禁止MIME类型嗅探")
    XSS_PROTECTION: bool = Field(default=True, description="是否启用XSS保护")

    class Config:
        env_prefix = "SECURITY_"


class PerformanceConfig(BaseModel):
    """性能配置"""

    # 图片处理配置
    IMAGE_QUALITY: int = 85

    # 数据库配置 - 主库（写）
    DATABASE_WRITE_URL: str = "mysql+aiomysql://root:your_password@localhost:your_port/nimbus"

    # 数据库配置 - 从库（读）
    DATABASE_READ_URLS: List[str] = []

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # 性能优化配置
    BATCH_SIZE: int = 1000  # 批量操作的默认大小
    MAX_PAGE_SIZE: int = 100  # 最大分页大小


class PasswordPolicyConfig(BaseModel):
    """密码策略配置"""

    min_length: int = Field(default=8, description="最小长度")
    max_length: int = Field(default=32, description="最大长度")
    require_uppercase: bool = Field(default=True, description="是否要求大写字母")
    require_lowercase: bool = Field(default=True, description="是否要求小写字母")
    require_numbers: bool = Field(default=True, description="是否要求数字")
    require_special_chars: bool = Field(default=True, description="是否要求特殊字符")
    special_chars: str = Field(default="!@#$%^&*()_+-=[]{}|;:,.<>?", description="允许的特殊字符")
    max_repeated_chars: int = Field(default=3, description="最大重复字符数")
    password_history: int = Field(default=5, description="密码历史记录数")
    expire_days: int = Field(default=90, description="密码过期天数")
    lock_duration: int = Field(default=30, description="账户锁定时长(分钟)")
    max_attempts: int = Field(default=5, description="最大尝试次数")


class TokenConfig(BaseModel):
    """令牌配置"""

    secret_key: str = Field(..., description="密钥")
    algorithm: str = Field(default="HS256", description="加密算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    refresh_token_expire_days: int = Field(default=7, description="刷新令牌过期时间(天)")
