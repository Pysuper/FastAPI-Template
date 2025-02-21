# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：system.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：系统管理模块

提供系统信息、配置、日志、监控等管理功能
支持系统备份、恢复、清理和优化
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from core.cache.config.config import CacheConfig
from core.db import get_db
from core.dependencies.permissions import requires_permissions
from core.dependencies.rate_limit import rate_limiter
from core.exceptions import NotFoundException, ValidationException
from core.security import get_current_user
from models.user import User
from schemas.common import Response
from services.system.system_service import SystemService

# 缓存配置
SYSTEM_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "system:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 3600,  # 缓存1小时
}

router = APIRouter(prefix="/system", tags=["系统管理"])


@router.get(
    "/info",
    response_model=Response[Dict[str, Any]],
    summary="获取系统信息",
    description="获取系统基本信息，包括版本、运行状态等",
)
@requires_permissions(["view_system_info"])
async def get_system_info(db: Session = Depends(async_db)) -> Response[Dict[str, Any]]:
    """获取系统信息

    Args:
        db: 数据库会话

    Returns:
        包含系统信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        info = await SystemService.get_system_info(db)
        return Response(code=200, message="获取系统信息成功", data=info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取系统信息失败: {str(e)}")


@router.get("/config", response_model=Response[Dict[str, Any]], summary="获取系统配置", description="获取系统配置信息")
@requires_permissions(["view_system_config"])
async def get_system_config(
    config_type: Optional[str] = Query(None, description="配置类型"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """获取系统配置

    Args:
        config_type: 可选的配置类型过滤
        db: 数据库会话

    Returns:
        包含系统配置的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        config = await SystemService.get_system_config(db, config_type=config_type)
        return Response(code=200, message="获取系统配置成功", data=config)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取系统配置失败: {str(e)}")


@router.put("/config", response_model=Response[Dict[str, Any]], summary="更新系统配置", description="更新系统配置信息")
@requires_permissions(["update_system_config"])
@rate_limiter(max_requests=5, window_seconds=300)  # 5分钟内最多5次更新请求
async def update_system_config(
    data: Dict[str, Any] = Body(..., description="系统配置数据"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """更新系统配置

    Args:
        data: 系统配置更新数据
        db: 数据库会话

    Returns:
        包含更新后的系统配置的响应对象

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        config = await SystemService.update_system_config(db, data)
        return Response(code=200, message="更新系统配置成功", data=config)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新系统配置失败: {str(e)}")


@router.get(
    "/logs",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取系统日志",
    description="获取系统日志记录，支持多种过滤条件",
)
@requires_permissions(["view_system_logs"])
async def get_system_logs(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    level: Optional[str] = Query(None, description="日志级别"),
    module: Optional[str] = Query(None, description="模块名称"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取系统日志

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        level: 可选的日志级别过滤
        module: 可选的模块名称过滤
        page: 页码，从1开始
        size: 每页记录数
        db: 数据库会话

    Returns:
        包含系统日志列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        logs = await SystemService.get_system_logs(
            db, skip=(page - 1) * size, limit=size, start_time=start_time, end_time=end_time, level=level, module=module
        )
        return Response(code=200, message="获取系统日志成功", data=logs)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取系统日志失败: {str(e)}")


@router.get(
    "/stats", response_model=Response[Dict[str, Any]], summary="获取系统统计", description="获取系统运行统计信息"
)
@requires_permissions(["view_system_stats"])
async def get_system_stats(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取系统统计

    Args:
        start_date: 可选的开始日期
        end_date: 可选的结束日期
        db: 数据库会话

    Returns:
        包含系统统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await SystemService.get_system_stats(db, start_date=start_date, end_date=end_date)
        return Response(code=200, message="获取系统统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取系统统计失败: {str(e)}")


@router.get(
    "/monitor", response_model=Response[Dict[str, Any]], summary="获取系统监控", description="获取系统实时监控信息"
)
@requires_permissions(["view_system_monitor"])
async def get_system_monitor(
    monitor_type: Optional[str] = Query(None, description="监控类型"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """获取系统监控

    Args:
        monitor_type: 可选的监控类型过滤
        db: 数据库会话

    Returns:
        包含系统监控信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        monitor_data = await SystemService.get_system_monitor(db, monitor_type=monitor_type)
        return Response(code=200, message="获取系统监控成功", data=monitor_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取系统监控失败: {str(e)}")


@router.post("/backup", response_model=Response[Dict[str, Any]], summary="系统备份", description="执行系统数据备份")
@requires_permissions(["backup_system"])
@rate_limiter(max_requests=1, window_seconds=3600)  # 每小时最多1次备份请求
async def backup_system(
    data: Dict[str, Any] = Body(..., description="备份配置数据"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """系统备份

    Args:
        data: 备份配置数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含备份结果的响应对象

    Raises:
        HTTPException: 备份失败时抛出
    """
    try:
        backup_info = await SystemService.backup_system(db, data)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(SystemService.send_backup_notification, backup_info)

        return Response(code=200, message="系统备份成功", data=backup_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"系统备份失败: {str(e)}")


@router.post("/restore", response_model=Response[Dict[str, Any]], summary="系统恢复", description="从备份恢复系统数据")
@requires_permissions(["restore_system"])
@rate_limiter(max_requests=1, window_seconds=3600)  # 每小时最多1次恢复请求
async def restore_system(
    data: Dict[str, Any] = Body(..., description="恢复配置数据"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """系统恢复

    Args:
        data: 恢复配置数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含恢复结果的响应对象

    Raises:
        HTTPException: 恢复失败时抛出
    """
    try:
        restore_info = await SystemService.restore_system(db, data)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(SystemService.send_restore_notification, restore_info)

        return Response(code=200, message="系统恢复成功", data=restore_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"系统恢复失败: {str(e)}")


@router.post("/cleanup", response_model=Response[Dict[str, Any]], summary="系统清理", description="清理系统冗余数据")
@requires_permissions(["cleanup_system"])
@rate_limiter(max_requests=1, window_seconds=86400)  # 每天最多1次清理请求
async def cleanup_system(
    data: Dict[str, Any] = Body(..., description="清理配置数据"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """系统清理

    Args:
        data: 清理配置数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含清理结果的响应对象

    Raises:
        HTTPException: 清理失败时抛出
    """
    try:
        cleanup_info = await SystemService.cleanup_system(db, data)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(SystemService.send_cleanup_notification, cleanup_info)

        return Response(code=200, message="系统清理成功", data=cleanup_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"系统清理失败: {str(e)}")


@router.post("/optimize", response_model=Response[Dict[str, Any]], summary="系统优化", description="执行系统性能优化")
@requires_permissions(["optimize_system"])
@rate_limiter(max_requests=1, window_seconds=86400)  # 每天最多1次优化请求
async def optimize_system(
    data: Dict[str, Any] = Body(..., description="优化配置数据"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """系统优化

    Args:
        data: 优化配置数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含优化结果的响应对象

    Raises:
        HTTPException: 优化失败时抛出
    """
    try:
        optimize_info = await SystemService.optimize_system(db, data)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(SystemService.send_optimize_notification, optimize_info)

        return Response(code=200, message="系统优化成功", data=optimize_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"系统优化失败: {str(e)}")


# 新增API端点
@router.get(
    "/health", response_model=Response[Dict[str, Any]], summary="系统健康检查", description="检查系统各组件的健康状态"
)
@requires_permissions(["view_system_health"])
async def check_system_health(
    check_type: Optional[str] = Query(None, description="检查类型"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """系统健康检查

    Args:
        check_type: 可选的检查类型过滤
        db: 数据库会话

    Returns:
        包含健康检查结果的响应对象

    Raises:
        HTTPException: 检查失败时抛出
    """
    try:
        health_info = await SystemService.check_system_health(db, check_type=check_type)
        return Response(code=200, message="系统健康检查成功", data=health_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"系统健康检查失败: {str(e)}")


@router.get(
    "/performance", response_model=Response[Dict[str, Any]], summary="系统性能分析", description="获取系统性能分析报告"
)
@requires_permissions(["view_system_performance"])
async def analyze_system_performance(
    metric_type: Optional[str] = Query(None, description="指标类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """系统性能分析

    Args:
        metric_type: 可选的指标类型过滤
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        db: 数据库会话

    Returns:
        包含性能分析结果的响应对象

    Raises:
        HTTPException: 分析失败时抛出
    """
    try:
        performance_info = await SystemService.analyze_system_performance(
            db, metric_type=metric_type, start_time=start_time, end_time=end_time
        )
        return Response(code=200, message="系统性能分析成功", data=performance_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"系统性能分析失败: {str(e)}")


@router.post(
    "/maintenance", response_model=Response[Dict[str, Any]], summary="系统维护", description="执行系统维护任务"
)
@requires_permissions(["maintain_system"])
@rate_limiter(max_requests=1, window_seconds=86400)  # 每天最多1次维护请求
async def maintain_system(
    data: Dict[str, Any] = Body(..., description="维护配置数据"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """系统维护

    Args:
        data: 维护配置数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含维护结果的响应对象

    Raises:
        HTTPException: 维护失败时抛出
    """
    try:
        maintenance_info = await SystemService.maintain_system(db, data)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(SystemService.send_maintenance_notification, maintenance_info)

        return Response(code=200, message="系统维护成功", data=maintenance_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"系统维护失败: {str(e)}")
