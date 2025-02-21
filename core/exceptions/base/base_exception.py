"""
基础异常模块
包含所有异常的基类定义
"""

from typing import Any, Dict, Optional

from fastapi import status
from fastapi.responses import JSONResponse


class BaseException(Exception):
    """统一的异常基类"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        safe_details: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化异常

        Args:
            code: 错误码
            message: 错误信息
            status_code: HTTP状态码
            details: 错误详情
            context: 错误上下文
            headers: 响应头
            safe_details: 安全的错误详情(可以返回给客户端)
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.context = context
        self.headers = headers
        self.safe_details = safe_details
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典格式

        Returns:
            包含异常信息的字典
        """
        return {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.safe_details or self.details,
        }

    def to_response(self) -> JSONResponse:
        """
        将异常转换为JSON响应

        Returns:
            FastAPI的JSON响应对象
        """
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict(),
            headers=self.headers,
        )
