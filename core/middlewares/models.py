from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """错误详情模型"""

    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class Pagination(BaseModel):
    """分页信息模型"""

    page: int = Field(1, description="当前页码")
    size: int = Field(10, description="每页大小")
    total: int = Field(0, description="总记录数")


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""

    success: bool = Field(True, description="是否成功")
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    error: Optional[ErrorDetail] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class PageResponse(BaseResponse[List[T]]):
    """分页响应模型"""

    pagination: Optional[Pagination] = Field(None, description="分页信息")


class MetricsData(BaseModel):
    """指标数据模型"""

    name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    labels: Dict[str, str] = Field(default_factory=dict, description="标签")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class HealthCheckResult(BaseModel):
    """健康检查结果模型"""

    status: str = Field(..., description="状态")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")


class AuditLog(BaseModel):
    """审计日志模型"""

    user_id: Optional[str] = Field(None, description="用户ID")
    action: str = Field(..., description="操作")
    resource: str = Field(..., description="资源")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    timestamp: datetime = Field(default_factory=datetime.now, description="操作时间")


class CacheInfo(BaseModel):
    """缓存信息模型"""

    key: str = Field(..., description="缓存键")
    value_type: str = Field(..., description="值类型")
    size: int = Field(..., description="大小(字节)")
    created_at: datetime = Field(..., description="创建时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    hits: int = Field(0, description="命中次数")
    last_accessed: Optional[datetime] = Field(None, description="最后访问时间")


class RateLimitInfo(BaseModel):
    """限流信息模型"""

    key: str = Field(..., description="限流键")
    limit: int = Field(..., description="限制次数")
    remaining: int = Field(..., description="剩余次数")
    reset_at: datetime = Field(..., description="重置时间")
    window: int = Field(..., description="时间窗口(秒)")


class PerformanceMetrics(BaseModel):
    """性能指标模型"""

    request_count: int = Field(0, description="请求总数")
    error_count: int = Field(0, description="错误总数")
    avg_response_time: float = Field(0.0, description="平均响应时间")
    max_response_time: float = Field(0.0, description="最大响应时间")
    min_response_time: float = Field(0.0, description="最小响应时间")
    active_requests: int = Field(0, description="活跃请求数")
    requests_per_second: float = Field(0.0, description="每秒请求数")


class SecurityEvent(BaseModel):
    """安全事件模型"""

    event_type: str = Field(..., description="事件类型")
    severity: str = Field(..., description="严重程度")
    source: str = Field(..., description="来源")
    description: str = Field(..., description="描述")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件时间")


def create_response(
    data: Optional[T] = None, message: str = "success", code: int = 200, error: Optional[ErrorDetail] = None
) -> BaseResponse[T]:
    """创建响应"""
    return BaseResponse(success=error is None, code=code, message=message, data=data, error=error)


def create_error_response(
    code: str, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = 400
) -> BaseResponse:
    """创建错误响应"""
    return BaseResponse(
        success=False, code=status_code, message=message, error=ErrorDetail(code=code, message=message, details=details)
    )


def create_page_response(
    items: List[T], total: int, page: int = 1, size: int = 10, message: str = "success"
) -> PageResponse[T]:
    """创建分页响应"""
    return PageResponse(
        success=True, code=200, message=message, data=items, pagination=Pagination(page=page, size=size, total=total)
    )
