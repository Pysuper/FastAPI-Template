"""
验证相关的HTTP异常模块
"""

from typing import Any, Dict, List, Optional

from fastapi import status

from core.exceptions.base.base_exception import BaseException
from core.exceptions.base.error_codes import ErrorCode


class ValidationException(BaseException):
    """验证异常基类"""

    def __init__(
        self,
        message: str = "数据验证失败",
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        初始化验证异常

        Args:
            message: 错误信息
            details: 错误详情
            context: 错误上下文
            errors: 验证错误列表
        """
        details = details or {}
        if errors:
            details["errors"] = errors

        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            context=context,
        )


class RequestValidationException(ValidationException):
    """请求验证异常"""

    def __init__(
        self,
        errors: List[Dict[str, Any]],
        message: str = "请求参数验证失败",
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化请求验证异常

        Args:
            errors: 验证错误列表
            message: 错误信息
            context: 错误上下文
        """
        context = {"request_validation": True, **(context or {})}
        super().__init__(
            message=message,
            errors=errors,
            context=context,
        )


class ModelValidationException(ValidationException):
    """模型验证异常"""

    def __init__(
        self,
        errors: List[Dict[str, Any]],
        message: str = "数据模型验证失败",
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化模型验证异常

        Args:
            errors: 验证错误列表
            message: 错误信息
            context: 错误上下文
        """
        context = {"model_validation": True, **(context or {})}
        super().__init__(
            message=message,
            errors=errors,
            context=context,
        )


class SchemaValidationException(ValidationException):
    """Schema验证异常"""

    def __init__(
        self,
        errors: List[Dict[str, Any]],
        message: str = "数据结构验证失败",
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化Schema验证异常

        Args:
            errors: 验证错误列表
            message: 错误信息
            context: 错误上下文
        """
        context = {"schema_validation": True, **(context or {})}
        super().__init__(
            message=message,
            errors=errors,
            context=context,
        )
