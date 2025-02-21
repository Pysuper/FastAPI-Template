import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.dependencies import async_db
from schemas.system import LogAggregationRequest, LogAggregationResponse, LogExportRequest
from security.core.security import get_current_user
from core.utils.log_manager import LogManager
from core.utils.logging import log_error, operation_log

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/export")
@operation_log("导出系统日志")
async def export_logs(
    request: LogExportRequest,
    db: Session = Depends(async_db),
    current_user: dict = Depends(get_current_user),
):
    """
    导出系统日志
    支持多种格式：CSV、JSON、Excel
    支持时间范围和其他过滤条件
    """
    try:
        log_manager = LogManager(db)
        result = log_manager.export_logs(
            format=request.format,
            start_time=request.start_time,
            end_time=request.end_time,
            level=request.level,
            module=request.module,
        )

        # 设置响应头
        filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if request.format.lower() == "csv":
            media_type = "text/csv"
            filename += ".csv"
        elif request.format.lower() == "json":
            media_type = "application/json"
            filename += ".json"
        elif request.format.lower() == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename += ".xlsx"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        return StreamingResponse(
            iter([result]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        log_error(f"Failed to export logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export logs")


@router.post("/analyze", response_model=LogAggregationResponse)
@operation_log("分析系统日志")
async def analyze_logs(
    request: LogAggregationRequest,
    db: Session = Depends(async_db),
    current_user: dict = Depends(get_current_user),
):
    """
    分析系统日志
    提供各种统计指标：
    - 错误率
    - 各级别日志数量
    - 模块分布
    - 时间趋势
    """
    try:
        log_manager = LogManager(db)
        result = log_manager.analyze_logs(
            start_time=request.start_time,
            end_time=request.end_time,
            group_by=request.group_by,
            metrics=request.metrics,
        )
        return result

    except Exception as e:
        log_error(f"Failed to analyze logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze logs")


class Log(BaseModel):
    """系统日志模型"""

    id: int
    level: str
    message: str
    module: str
    timestamp: datetime
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True


class LogCreate(BaseModel):
    """创建日志模型"""

    level: str
    message: str
    module: str
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class LogUpdate(BaseModel):
    """更新日志模型"""

    level: Optional[str] = None
    message: Optional[str] = None
    module: Optional[str] = None


class LogFilter(BaseModel):
    """日志过滤模型"""

    level: Optional[str] = None
    module: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
