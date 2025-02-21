"""
文件处理相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class FileBusinessException(BusinessException):
    """文件处理业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.FILE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化文件处理业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"file_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class FileNotFoundException(FileBusinessException):
    """文件不存在异常"""

    def __init__(
        self,
        message: str = "文件不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"file_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class FileUploadException(FileBusinessException):
    """文件上传异常"""

    def __init__(
        self,
        message: str = "文件上传失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"upload_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class FileDownloadException(FileBusinessException):
    """文件下载异常"""

    def __init__(
        self,
        message: str = "文件下载失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"download_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class FileSizeException(FileBusinessException):
    """文件大小异常"""

    def __init__(
        self,
        message: str = "文件大小超限",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"size_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class FileTypeException(FileBusinessException):
    """文件类型异常"""

    def __init__(
        self,
        message: str = "文件类型不支持",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"type_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class FileStorageException(FileBusinessException):
    """文件存储异常"""

    def __init__(
        self,
        message: str = "文件存储失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"storage_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
