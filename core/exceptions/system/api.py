"""
API相关的系统异常模块
"""

from typing import Dict, Optional

from fastapi import status

from core.exceptions.base.base_exception import BaseException
from core.exceptions.base.error_codes import ErrorCode


class SystemException(BaseException):
    """系统异常基类"""

    def __init__(
        self,
        code: str = ErrorCode.SYSTEM_ERROR,
        message: str = "系统错误",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        初始化系统异常

        Args:
            code: 错误码
            message: 错误信息
            status_code: HTTP状态码
            details: 错误详情
            context: 错误上下文
            headers: 响应头
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status_code,
            details=details,
            context=context,
            headers=headers,
        )


class APIException(SystemException):
    """API异常"""

    def __init__(
        self,
        message: str = "API错误",
        code: str = ErrorCode.SYSTEM_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化API异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=code,
            message=message,
            details=details,
            context={"api_error": True, **(context or {})},
        )


class BusinessException(SystemException):
    """业务逻辑异常"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.BUSINESS_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化业务逻辑异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            context={"business_error": True, **(context or {})},
        )


class ThirdPartyException(SystemException):
    """第三方服务异常"""

    def __init__(
        self,
        message: str = "第三方服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化第三方服务异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=ErrorCode.THIRD_PARTY_ERROR,
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
            context={"third_party_error": True, **(context or {})},
        )


class RateLimitException(SystemException):
    """限流异常"""

    def __init__(
        self,
        message: str = "请求过于频繁",
        code: str = ErrorCode.RATE_LIMIT_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化限流异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            context={"rate_limit_error": True, **(context or {})},
        )


class SecurityException(SystemException):
    """安全异常"""

    def __init__(
        self,
        message: str = "安全错误",
        code: str = ErrorCode.SECURITY_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化安全异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            context={"security_error": True, **(context or {})},
        )


class FileException(SystemException):
    """文件操作异常"""

    def __init__(
        self,
        message: str = "文件操作失败",
        code: str = ErrorCode.FILE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化文件操作异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            context={"file_error": True, **(context or {})},
        )
