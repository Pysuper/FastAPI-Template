"""
请求相关的HTTP异常模块
"""

from typing import Any, Dict, Optional

from fastapi import status

from core.exceptions.base.base_exception import BaseException
from core.exceptions.base.error_codes import ErrorCode


class HTTPException(BaseException):
    """HTTP异常基类"""

    def __init__(
        self,
        code: str = ErrorCode.HTTP_ERROR,
        message: str = "HTTP错误",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        初始化HTTP异常

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


class BadRequestException(HTTPException):
    """错误的请求异常"""

    def __init__(
        self,
        message: str = "错误的请求",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化错误请求异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=ErrorCode.BAD_REQUEST,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            context=context,
        )


class NotFoundException(HTTPException):
    """资源不存在异常"""

    def __init__(
        self,
        message: str = "资源不存在",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化资源不存在异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            context=context,
        )


class MethodNotAllowedException(HTTPException):
    """方法不允许异常"""

    def __init__(
        self,
        message: str = "方法不允许",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化方法不允许异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
        """
        super().__init__(
            code=ErrorCode.METHOD_NOT_ALLOWED,
            message=message,
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            details=details,
            context=context,
        )


class TooManyRequestsException(HTTPException):
    """请求过多异常"""

    def __init__(
        self,
        message: str = "请求过于频繁",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        """
        初始化请求过多异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
            retry_after: 重试等待时间
        """
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)

        super().__init__(
            code=ErrorCode.TOO_MANY_REQUESTS,
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            context=context,
            headers=headers,
        )
