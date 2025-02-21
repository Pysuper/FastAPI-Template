"""
Excel处理服务相关的异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class ExcelException(BusinessException):
    """Excel处理服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.THIRD_PARTY_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化Excel处理服务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"excel_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class ExcelReadException(ExcelException):
    """Excel读取异常"""

    def __init__(
        self,
        message: str = "Excel读取失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"read_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExcelWriteException(ExcelException):
    """Excel写入异常"""

    def __init__(
        self,
        message: str = "Excel写入失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"write_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExcelFormatException(ExcelException):
    """Excel格式异常"""

    def __init__(
        self,
        message: str = "Excel格式错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"format_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExcelTemplateException(ExcelException):
    """Excel模板异常"""

    def __init__(
        self,
        message: str = "Excel模板错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"template_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExcelDataException(ExcelException):
    """Excel数据异常"""

    def __init__(
        self,
        message: str = "Excel数据错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"data_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExcelValidationException(ExcelException):
    """Excel验证异常"""

    def __init__(
        self,
        message: str = "Excel验证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"validation_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExcelConversionException(ExcelException):
    """Excel转换异常"""

    def __init__(
        self,
        message: str = "Excel转换失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"conversion_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExcelSizeException(ExcelException):
    """Excel大小异常"""

    def __init__(
        self,
        message: str = "Excel文件过大",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"size_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
