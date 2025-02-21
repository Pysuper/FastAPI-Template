"""
认证相关的HTTP异常模块
"""

from typing import Any, Dict, Optional

from fastapi import status

from core.exceptions.base.base_exception import BaseException
from core.exceptions.base.error_codes import ErrorCode


class AuthenticationException(BaseException):
    """认证异常基类"""

    def __init__(
        self,
        message: str = "认证失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化认证异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=ErrorCode.AUTHENTICATION_ERROR,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            context=context,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationException(BaseException):
    """授权异常"""

    def __init__(
        self,
        message: str = "没有权限",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化授权异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=ErrorCode.AUTHORIZATION_ERROR,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            context=context,
        )


class TokenException(AuthenticationException):
    """令牌异常"""

    def __init__(
        self,
        message: str = "无效的令牌",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化令牌异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"token_error": True, **(context or {})}
        super().__init__(
            message=message,
            details=details,
            context=context,
        )


class CredentialsException(AuthenticationException):
    """凭证异常"""

    def __init__(
        self,
        message: str = "无效的凭证",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化凭证异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        context = {"credentials_error": True, **(context or {})}
        super().__init__(
            message=message,
            details=details,
            context=context,
        )
