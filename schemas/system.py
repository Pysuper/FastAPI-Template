from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class LogExportRequest(BaseModel):
    """日志导出请求"""
    model_config = ConfigDict(
        title="日志导出请求",
        json_schema_extra={
            "description": "用于导出系统日志的请求参数"
        }
    )

    format: str = Field(..., description="导出格式：csv, json, excel")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    level: Optional[str] = Field(None, description="日志级别")
    module: Optional[str] = Field(None, description="模块名称")

class LogAggregationRequest(BaseModel):
    """日志聚合分析请求"""
    model_config = ConfigDict(
        title="日志聚合分析请求",
        json_schema_extra={
            "description": "用于分析系统日志的请求参数"
        }
    )

    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    group_by: Optional[List[str]] = Field(default=["level", "module"], description="分组字段")
    metrics: Optional[List[str]] = Field(
        default=["count", "error_rate"],
        description="统计指标"
    )

class LogAggregationResponse(BaseModel):
    """日志聚合分析响应"""
    model_config = ConfigDict(
        title="日志聚合分析响应",
        json_schema_extra={
            "description": "日志聚合分析结果"
        }
    )

    total_logs: int = Field(..., description="总日志数")
    error_rate: float = Field(..., description="错误率")
    level_distribution: Dict[str, int] = Field(..., description="日志级别分布")
    module_distribution: Dict[str, int] = Field(..., description="模块分布")
    time_trend: Dict[str, int] = Field(..., description="时间趋势")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间") 