from enum import Enum


class SecurityLevel(str, Enum):
    """安全级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(str, Enum):
    """审计事件类型"""

    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_ALERT = "security_alert"


class PermissionLevel(str, Enum):
    """权限级别"""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class RateLimitType(str, Enum):
    """限流类型"""

    IP = "ip"
    USER = "user"
    API = "api"
    GLOBAL = "global"


class EncryptionType(str, Enum):
    """加密类型"""

    NONE = "none"
    BASE64 = "base64"
    AES = "aes"
    RSA = "rsa"


# 安全相关常量
SECURITY_CONSTANTS = {
    # 密码相关
    "MIN_PASSWORD_LENGTH": 8,
    "MAX_PASSWORD_LENGTH": 32,
    "PASSWORD_COMPLEXITY_REGEX": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]",
    # 会话相关
    "SESSION_TIMEOUT": 3600,  # 1小时
    "MAX_SESSIONS_PER_USER": 5,
    # 限流相关
    "DEFAULT_RATE_LIMIT": 100,  # 每分钟请求数
    "RATE_LIMIT_WINDOW": 60,  # 时间窗口（秒）
    # 审计相关
    "AUDIT_LOG_RETENTION": 90,  # 日志保留天数
    "MAX_AUDIT_BATCH_SIZE": 1000,
    # 加密相关
    "DEFAULT_ENCRYPTION_TYPE": EncryptionType.AES,
    "KEY_ROTATION_INTERVAL": 30,  # 密钥轮换间隔（天）
    # 其他安全设置
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOCKOUT_DURATION": 900,  # 15分钟
    "SECURE_HEADERS": {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    },
}
