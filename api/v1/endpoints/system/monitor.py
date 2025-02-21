# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：monitor.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：系统监控模块

提供系统资源监控和性能分析功能
支持实时监控和历史数据查询
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from core.dependencies.rate_limit import rate_limiter
from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from schemas.common import Response
from services.monitor.monitor_service import MonitorService
from sqlalchemy.orm import Session

from core.cache.config.config import CacheConfig
from core.db import get_db
from core.dependencies.permissions import requires_permissions

# 缓存配置
MONITOR_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "monitor:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 300,  # 缓存5分钟
}

router = APIRouter(prefix="/monitor", tags=["系统监控"])


@router.get(
    "/system", response_model=Response[Dict[str, Any]], summary="获取系统监控", description="获取系统整体运行状态监控"
)
@requires_permissions(["view_system_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_system_monitor(db: Session = Depends(async_db)) -> Response[Dict[str, Any]]:
    """获取系统监控

    Args:
        db: 数据库会话

    Returns:
        包含系统监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_system_monitor(db)
        return Response(code=200, message="获取系统监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取系统监控失败: {str(e)}")


@router.get(
    "/cpu", response_model=Response[Dict[str, Any]], summary="获取CPU监控", description="获取CPU使用率和负载监控"
)
@requires_permissions(["view_cpu_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_cpu_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取CPU监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        db: 数据库会话

    Returns:
        包含CPU监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_cpu_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval
        )
        return Response(code=200, message="获取CPU监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取CPU监控失败: {str(e)}")


@router.get(
    "/memory", response_model=Response[Dict[str, Any]], summary="获取内存监控", description="获取内存使用率和分配监控"
)
@requires_permissions(["view_memory_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_memory_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取内存监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        db: 数据库会话

    Returns:
        包含内存监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_memory_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval
        )
        return Response(code=200, message="获取内存监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取内存监控失败: {str(e)}")


@router.get(
    "/disk", response_model=Response[Dict[str, Any]], summary="获取磁盘监控", description="获取磁盘使用率和IO监控"
)
@requires_permissions(["view_disk_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_disk_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    mount_point: Optional[str] = Query(None, description="挂载点"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取磁盘监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        mount_point: 可选的挂载点过滤
        db: 数据库会话

    Returns:
        包含磁盘监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_disk_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval, mount_point=mount_point
        )
        return Response(code=200, message="获取磁盘监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取磁盘监控失败: {str(e)}")


@router.get(
    "/network", response_model=Response[Dict[str, Any]], summary="获取网络监控", description="获取网络流量和连接监控"
)
@requires_permissions(["view_network_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_network_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    interface: Optional[str] = Query(None, description="网络接口"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取网络监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        interface: 可选的网络接口过滤
        db: 数据库会话

    Returns:
        包含网络监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_network_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval, interface=interface
        )
        return Response(code=200, message="获取网络监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取网络监控失败: {str(e)}")


@router.get(
    "/database",
    response_model=Response[Dict[str, Any]],
    summary="获取数据库监控",
    description="获取数据库性能和连接监控",
)
@requires_permissions(["view_database_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_database_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    db_name: Optional[str] = Query(None, description="数据库名称"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取数据库监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        db_name: 可选的数据库名称过滤
        db: 数据库会话

    Returns:
        包含数据库监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_database_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval, db_name=db_name
        )
        return Response(code=200, message="获取数据库监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取数据库监控失败: {str(e)}")


@router.get(
    "/cache", response_model=Response[Dict[str, Any]], summary="获取缓存监控", description="获取缓存使用率和命中率监控"
)
@requires_permissions(["view_cache_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_cache_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    cache_type: Optional[str] = Query(None, description="缓存类型"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取缓存监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        cache_type: 可选的缓存类型过滤
        db: 数据库会话

    Returns:
        包含缓存监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_cache_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval, cache_type=cache_type
        )
        return Response(code=200, message="获取缓存监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取缓存监控失败: {str(e)}")


@router.get(
    "/queue",
    response_model=Response[Dict[str, Any]],
    summary="获取队列监控",
    description="获取消息队列长度和处理率监控",
)
@requires_permissions(["view_queue_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_queue_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    queue_name: Optional[str] = Query(None, description="队列名称"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取队列监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        queue_name: 可选的队列名称过滤
        db: 数据库会话

    Returns:
        包含队列监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_queue_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval, queue_name=queue_name
        )
        return Response(code=200, message="获取队列监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取队列监控失败: {str(e)}")


@router.get(
    "/api", response_model=Response[Dict[str, Any]], summary="获取API监控", description="获取API请求量和响应时间监控"
)
@requires_permissions(["view_api_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_api_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    endpoint: Optional[str] = Query(None, description="API端点"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取API监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        endpoint: 可选的API端点过滤
        db: 数据库会话

    Returns:
        包含API监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_api_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval, endpoint=endpoint
        )
        return Response(code=200, message="获取API监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取API监控失败: {str(e)}")


@router.get(
    "/error", response_model=Response[Dict[str, Any]], summary="获取错误监控", description="获取系统错误和异常监控"
)
@requires_permissions(["view_error_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_error_monitor(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    interval: str = Query("1m", description="统计间隔"),
    error_type: Optional[str] = Query(None, description="错误类型"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取错误监控

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        interval: 统计间隔(1s/1m/5m/15m/1h)
        error_type: 可选的错误类型过滤
        db: 数据库会话

    Returns:
        包含错误监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_error_monitor(
            db, start_time=start_time, end_time=end_time, interval=interval, error_type=error_type
        )
        return Response(code=200, message="获取错误监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取错误监控失败: {str(e)}")


# 新增API端点
@router.get(
    "/process",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取进程监控",
    description="获取系统进程资源使用监控",
)
@requires_permissions(["view_process_monitor"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_process_monitor(
    process_name: Optional[str] = Query(None, description="进程名称"),
    sort_by: str = Query("cpu", description="排序字段"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取进程监控

    Args:
        process_name: 可选的进程名称过滤
        sort_by: 排序字段(cpu/memory/io)
        limit: 返回数量
        db: 数据库会话

    Returns:
        包含进程监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await MonitorService.get_process_monitor(
            db, process_name=process_name, sort_by=sort_by, limit=limit
        )
        return Response(code=200, message="获取进程监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取进程监控失败: {str(e)}")


@router.get(
    "/alerts", response_model=Response[List[Dict[str, Any]]], summary="获取告警信息", description="获取系统监控告警信息"
)
@requires_permissions(["view_monitor_alerts"])
async def get_monitor_alerts(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    alert_level: Optional[str] = Query(None, description="告警级别"),
    alert_type: Optional[str] = Query(None, description="告警类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取告警信息

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        alert_level: 可选的告警级别过滤
        alert_type: 可选的告警类型过滤
        page: 页码，从1开始
        page_size: 每页记录数
        db: 数据库会话

    Returns:
        包含告警信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        alerts = await MonitorService.get_monitor_alerts(
            db,
            start_time=start_time,
            end_time=end_time,
            alert_level=alert_level,
            alert_type=alert_type,
            skip=(page - 1) * page_size,
            limit=page_size,
        )
        return Response(code=200, message="获取告警信息成功", data=alerts)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取告警信息失败: {str(e)}")


@router.post(
    "/alerts/rules", response_model=Response[Dict[str, Any]], summary="设置告警规则", description="设置系统监控告警规则"
)
@requires_permissions(["manage_monitor_alerts"])
async def set_alert_rules(
    rules: Dict[str, Any] = Query(..., description="告警规则配置"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """设置告警规则

    Args:
        rules: 告警规则配置
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含告警规则设置结果的响应对象

    Raises:
        HTTPException: 设置失败时抛出
    """
    try:
        result = await MonitorService.set_alert_rules(db, rules)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(MonitorService.apply_alert_rules, result)

        return Response(code=200, message="设置告警规则成功", data=result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"设置告警规则失败: {str(e)}")
