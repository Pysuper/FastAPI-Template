"""
搜索服务相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class SearchServiceException(BusinessException):
    """搜索服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.THIRD_PARTY_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化搜索服务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"search_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class ElasticsearchException(SearchServiceException):
    """Elasticsearch异常基类"""

    def __init__(
        self,
        message: str = "Elasticsearch服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"elasticsearch_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class IndexException(SearchServiceException):
    """索引异常"""

    def __init__(
        self,
        message: str = "索引操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"index_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryException(SearchServiceException):
    """查询异常"""

    def __init__(
        self,
        message: str = "查询操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"query_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class BulkException(SearchServiceException):
    """批量操作异常"""

    def __init__(
        self,
        message: str = "批量操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"bulk_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MappingException(SearchServiceException):
    """映射异常"""

    def __init__(
        self,
        message: str = "映射操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"mapping_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AggregationException(SearchServiceException):
    """聚合异常"""

    def __init__(
        self,
        message: str = "聚合操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"aggregation_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ScrollException(SearchServiceException):
    """滚动查询异常"""

    def __init__(
        self,
        message: str = "滚动查询失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"scroll_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AnalyzerException(SearchServiceException):
    """分析器异常"""

    def __init__(
        self,
        message: str = "分析器操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"analyzer_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 