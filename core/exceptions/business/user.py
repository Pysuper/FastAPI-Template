"""
用户相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class UserBusinessException(BusinessException):
    """用户业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.USER_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化用户业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"user_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class UserNotFoundException(UserBusinessException):
    """用户不存在异常"""

    def __init__(
        self,
        message: str = "用户不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"user_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class UserAlreadyExistsException(UserBusinessException):
    """用户已存在异常"""

    def __init__(
        self,
        message: str = "用户已存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"user_exists": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class InvalidUserStatusException(UserBusinessException):
    """用户状态无效异常"""

    def __init__(
        self,
        message: str = "用户状态无效",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"invalid_status": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class UserProfileException(UserBusinessException):
    """用户资料异常"""

    def __init__(
        self,
        message: str = "用户资料错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"profile_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class UserSettingsException(UserBusinessException):
    """用户设置异常"""

    def __init__(
        self,
        message: str = "用户设置错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"settings_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
