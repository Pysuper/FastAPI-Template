"""
认证授权相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class AuthBusinessException(BusinessException):
    """认证授权业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.BUSINESS_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化认证授权业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"auth_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class LoginFailedException(AuthBusinessException):
    """登录失败异常"""

    def __init__(
        self,
        message: str = "登录失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"login_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AccountLockedException(AuthBusinessException):
    """账号锁定异常"""

    def __init__(
        self,
        message: str = "账号已被锁定",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"account_locked": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PasswordExpiredException(AuthBusinessException):
    """密码过期异常"""

    def __init__(
        self,
        message: str = "密码已过期",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"password_expired": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class InvalidVerificationCodeException(AuthBusinessException):
    """验证码无效异常"""

    def __init__(
        self,
        message: str = "验证码无效",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"invalid_code": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class SessionExpiredException(AuthBusinessException):
    """会话过期异常"""

    def __init__(
        self,
        message: str = "会话已过期",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"session_expired": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
