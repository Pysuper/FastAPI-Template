"""
日志服务相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class LoggingException(BusinessException):
    """日志服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.THIRD_PARTY_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化日志服务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"logging_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class ElasticsearchException(LoggingException):
    """Elasticsearch异常基类"""

    def __init__(
        self,
        message: str = "Elasticsearch服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"elasticsearch_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class LogstashException(LoggingException):
    """Logstash异常基类"""

    def __init__(
        self,
        message: str = "Logstash服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"logstash_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class KibanaException(LoggingException):
    """Kibana异常基类"""

    def __init__(
        self,
        message: str = "Kibana服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"kibana_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class LokiException(LoggingException):
    """Loki异常基类"""

    def __init__(
        self,
        message: str = "Loki服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"loki_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class LogCollectionException(LoggingException):
    """日志采集异常"""

    def __init__(
        self,
        message: str = "日志采集失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"collection_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class LogParsingException(LoggingException):
    """日志解析异常"""

    def __init__(
        self,
        message: str = "日志解析失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"parsing_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class LogStorageException(LoggingException):
    """日志存储异常"""

    def __init__(
        self,
        message: str = "日志存储失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"storage_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class LogQueryException(LoggingException):
    """日志查询异常"""

    def __init__(
        self,
        message: str = "日志查询失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"query_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class LogRotationException(LoggingException):
    """日志轮转异常"""

    def __init__(
        self,
        message: str = "日志轮转失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"rotation_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 