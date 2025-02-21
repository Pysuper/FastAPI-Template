"""
监控服务相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class MonitorException(BusinessException):
    """监控服务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.THIRD_PARTY_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化监控服务异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"monitor_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class PrometheusException(MonitorException):
    """Prometheus异常基类"""

    def __init__(
        self,
        message: str = "Prometheus服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"prometheus_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class GrafanaException(MonitorException):
    """Grafana异常基类"""

    def __init__(
        self,
        message: str = "Grafana服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"grafana_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MetricException(MonitorException):
    """指标异常"""

    def __init__(
        self,
        message: str = "指标采集失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"metric_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AlertException(MonitorException):
    """告警异常"""

    def __init__(
        self,
        message: str = "告警处理失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"alert_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class DashboardException(MonitorException):
    """仪表盘异常"""

    def __init__(
        self,
        message: str = "仪表盘操作失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"dashboard_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class QueryException(MonitorException):
    """查询异常"""

    def __init__(
        self,
        message: str = "监控数据查询失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"query_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ExporterException(MonitorException):
    """Exporter异常"""

    def __init__(
        self,
        message: str = "Exporter服务异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"exporter_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class RuleException(MonitorException):
    """规则异常"""

    def __init__(
        self,
        message: str = "监控规则异常",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"rule_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class NotificationException(MonitorException):
    """通知异常"""

    def __init__(
        self,
        message: str = "监控通知发送失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"notification_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 