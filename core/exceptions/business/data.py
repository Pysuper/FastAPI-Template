"""
数据导入导出相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class DataBusinessException(BusinessException):
    """数据处理业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.DATA_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化数据处理业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"data_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class DataImportException(DataBusinessException):
    """数据导入异常"""

    def __init__(
        self,
        message: str = "数据导入失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"import_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DataExportException(DataBusinessException):
    """数据导出异常"""

    def __init__(
        self,
        message: str = "数据导出失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"export_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DataValidationException(DataBusinessException):
    """数据验证异常"""

    def __init__(
        self,
        message: str = "数据验证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"validation_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DataFormatException(DataBusinessException):
    """数据格式异常"""

    def __init__(
        self,
        message: str = "数据格式错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"format_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DataSyncException(DataBusinessException):
    """数据同步异常"""

    def __init__(
        self,
        message: str = "数据同步失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"sync_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DataMigrationException(DataBusinessException):
    """数据迁移异常"""

    def __init__(
        self,
        message: str = "数据迁移失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"migration_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DataConversionException(DataBusinessException):
    """数据转换异常"""

    def __init__(
        self,
        message: str = "数据转换失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"conversion_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
