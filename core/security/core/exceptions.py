from typing import Any, Dict, Optional


class SecurityException(Exception):
    """基础安全异常"""

    def __init__(self, message: str, code: str = "SECURITY_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(SecurityException):
    """认证错误"""

    def __init__(self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(SecurityException):
    """授权错误"""

    def __init__(self, message: str = "没有权限", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class RateLimitExceeded(SecurityException):
    """超出请求限制"""

    def __init__(
        self, 
        message: str = "请求过于频繁", 
        details: Optional[Dict[str, Any]] = None,
        wait_time: Optional[int] = None
    ):
        if wait_time:
            message = f"{message}，请等待 {wait_time} 秒后重试"
            details = details or {}
            details["wait_time"] = wait_time
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)


class InvalidToken(SecurityException):
    """无效的令牌"""

    def __init__(self, message: str = "无效的令牌", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INVALID_TOKEN", details)


class TokenExpired(SecurityException):
    """令牌过期"""

    def __init__(self, message: str = "令牌已过期", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TOKEN_EXPIRED", details)


class PasswordPolicyViolation(SecurityException):
    """密码策略违规"""

    def __init__(self, message: str = "密码不符合安全要求", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PASSWORD_POLICY_VIOLATION", details)


class AccountLocked(SecurityException):
    """账户锁定"""

    def __init__(self, message: str = "账户已锁定", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ACCOUNT_LOCKED", details)


class InvalidSecurityContext(SecurityException):
    """无效的安全上下文"""

    def __init__(self, message: str = "无效的安全上下文", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INVALID_SECURITY_CONTEXT", details)


class EncryptionError(SecurityException):
    """加密错误"""

    def __init__(self, message: str = "加密操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ENCRYPTION_ERROR", details)


class DecryptionError(SecurityException):
    """解密错误"""

    def __init__(self, message: str = "解密操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DECRYPTION_ERROR", details)


class AuditLogError(SecurityException):
    """审计日志错误"""

    def __init__(self, message: str = "审计日志操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUDIT_LOG_ERROR", details)
