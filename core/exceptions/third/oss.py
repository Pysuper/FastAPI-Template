"""
对象存储服务相关的异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class OSSException(BusinessException):
    """对象存储服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.STORAGE_SERVICE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化对象存储服务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"oss_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class OSSUploadException(OSSException):
    """对象上传异常"""

    def __init__(
        self,
        message: str = "对象上传失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"upload_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class OSSDownloadException(OSSException):
    """对象下载异常"""

    def __init__(
        self,
        message: str = "对象下载失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"download_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class OSSDeleteException(OSSException):
    """对象删除异常"""

    def __init__(
        self,
        message: str = "对象删除失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"delete_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class OSSConfigException(OSSException):
    """对象存储配置异常"""

    def __init__(
        self,
        message: str = "对象存储配置错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"config_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class OSSAuthenticationException(OSSException):
    """对象存储认证异常"""

    def __init__(
        self,
        message: str = "对象存储认证失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"authentication_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class OSSQuotaException(OSSException):
    """对象存储配额异常"""

    def __init__(
        self,
        message: str = "对象存储配额超限",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"quota_exceeded": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class OSSBucketException(OSSException):
    """存储桶异常"""

    def __init__(
        self,
        message: str = "存储桶操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"bucket_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class OSSObjectException(OSSException):
    """存储对象异常"""

    def __init__(
        self,
        message: str = "存储对象操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"object_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
