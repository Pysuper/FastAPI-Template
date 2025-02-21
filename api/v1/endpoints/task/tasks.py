# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：tasks.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：任务管理模块

提供任务的创建、执行、监控和管理功能
支持任务调度、状态追踪和日志记录
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from core.cache.config.config import CacheConfig
from core.db import get_db
from core.exceptions import NotFoundException, ValidationException
from core.dependencies.permissions import requires_permissions
from core.dependencies.rate_limit import rate_limiter
from core.security import get_current_user
from models.task import Task
from schemas.task import TaskCreate, TaskUpdate, TaskFilter, TaskResponse
from schemas.common import Response
from services.task.task_service import TaskService
from .crud import CRUDRouter

# 缓存配置
TASK_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "task:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 300,  # 缓存5分钟
}

router = CRUDRouter(
    model=Task,
    create_schema=TaskCreate,
    update_schema=TaskUpdate,
    filter_schema=TaskFilter,
    prefix="/tasks",
    tags=["任务管理"],
)


@router.router.get(
    "/types",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取任务类型列表",
    description="获取系统支持的所有任务类型",
)
@requires_permissions(["view_task_types"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_task_types(db: Session = Depends(async_db)) -> Response[List[Dict[str, Any]]]:
    """获取任务类型列表

    Args:
        db: 数据库会话

    Returns:
        包含任务类型列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        task_types = await TaskService.get_task_types(db)
        return Response(code=200, message="获取任务类型列表成功", data=task_types)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取任务类型列表失败: {str(e)}")


@router.router.get(
    "/status",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取任务状态列表",
    description="获取系统定义的所有任务状态",
)
@requires_permissions(["view_task_status"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_task_status(db: Session = Depends(async_db)) -> Response[List[Dict[str, Any]]]:
    """获取任务状态列表

    Args:
        db: 数据库会话

    Returns:
        包含任务状态列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        task_status = await TaskService.get_task_status(db)
        return Response(code=200, message="获取任务状态列表成功", data=task_status)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取任务状态列表失败: {str(e)}")


@router.router.post("/start", response_model=Response[Dict[str, Any]], summary="启动任务", description="启动指定的任务")
@requires_permissions(["manage_tasks"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def start_task(
    task_id: int = Query(..., description="任务ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """启动任务

    Args:
        task_id: 任务ID
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含任务启动结果的响应对象

    Raises:
        HTTPException: 启动失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        result = await TaskService.start_task(db, task_id)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(TaskService.monitor_task_execution, task_id, result)

        return Response(code=200, message="启动任务成功", data=result)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"启动任务失败: {str(e)}")


@router.router.post("/stop", response_model=Response[Dict[str, Any]], summary="停止任务", description="停止指定的任务")
@requires_permissions(["manage_tasks"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def stop_task(
    task_id: int = Query(..., description="任务ID"),
    force: bool = Query(False, description="是否强制停止"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """停止任务

    Args:
        task_id: 任务ID
        force: 是否强制停止
        db: 数据库会话

    Returns:
        包含任务停止结果的响应对象

    Raises:
        HTTPException: 停止失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        result = await TaskService.stop_task(db, task_id, force=force)
        return Response(code=200, message="停止任务成功", data=result)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"停止任务失败: {str(e)}")


@router.router.post(
    "/restart", response_model=Response[Dict[str, Any]], summary="重启任务", description="重新启动指定的任务"
)
@requires_permissions(["manage_tasks"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def restart_task(
    task_id: int = Query(..., description="任务ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """重启任务

    Args:
        task_id: 任务ID
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含任务重启结果的响应对象

    Raises:
        HTTPException: 重启失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        result = await TaskService.restart_task(db, task_id)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(TaskService.monitor_task_execution, task_id, result)

        return Response(code=200, message="重启任务成功", data=result)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"重启任务失败: {str(e)}")


@router.router.post("/pause", response_model=Response[Dict[str, Any]], summary="暂停任务", description="暂停指定的任务")
@requires_permissions(["manage_tasks"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def pause_task(
    task_id: int = Query(..., description="任务ID"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """暂停任务

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        包含任务暂停结果的响应对象

    Raises:
        HTTPException: 暂停失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        result = await TaskService.pause_task(db, task_id)
        return Response(code=200, message="暂停任务成功", data=result)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"暂停任务失败: {str(e)}")


@router.router.post(
    "/resume", response_model=Response[Dict[str, Any]], summary="恢复任务", description="恢复已暂停的任务"
)
@requires_permissions(["manage_tasks"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def resume_task(
    task_id: int = Query(..., description="任务ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """恢复任务

    Args:
        task_id: 任务ID
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含任务恢复结果的响应对象

    Raises:
        HTTPException: 恢复失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        result = await TaskService.resume_task(db, task_id)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(TaskService.monitor_task_execution, task_id, result)

        return Response(code=200, message="恢复任务成功", data=result)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"恢复任务失败: {str(e)}")


@router.router.get(
    "/logs", response_model=Response[List[Dict[str, Any]]], summary="获取任务日志", description="获取指定任务的执行日志"
)
@requires_permissions(["view_task_logs"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_task_logs(
    task_id: int = Query(..., description="任务ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    level: Optional[str] = Query(None, description="日志级别"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取任务日志

    Args:
        task_id: 任务ID
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        level: 可选的日志级别过滤
        page: 页码，从1开始
        size: 每页记录数
        db: 数据库会话

    Returns:
        包含任务日志的响应对象

    Raises:
        HTTPException: 查询失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        logs = await TaskService.get_task_logs(
            db,
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            level=level,
            skip=(page - 1) * size,
            limit=size,
        )
        return Response(code=200, message="获取任务日志成功", data=logs)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取任务日志失败: {str(e)}")


@router.router.get(
    "/stats", response_model=Response[Dict[str, Any]], summary="获取任务统计", description="获取指定任务的执行统计信息"
)
@requires_permissions(["view_task_stats"])
@rate_limiter(max_requests=60, window_seconds=60)  # 每分钟最多60次请求
async def get_task_stats(
    task_id: int = Query(..., description="任务ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取任务统计

    Args:
        task_id: 任务ID
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        db: 数据库会话

    Returns:
        包含任务统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        stats = await TaskService.get_task_stats(db, task_id=task_id, start_time=start_time, end_time=end_time)
        return Response(code=200, message="获取任务统计成功", data=stats)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取任务统计失败: {str(e)}")


# 新增API端点
@router.router.post(
    "/batch/start",
    response_model=Response[List[Dict[str, Any]]],
    summary="批量启动任务",
    description="批量启动多个任务",
)
@requires_permissions(["manage_tasks"])
@rate_limiter(max_requests=30, window_seconds=60)  # 每分钟最多30次请求
async def batch_start_tasks(
    task_ids: List[int] = Body(..., description="任务ID列表"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """批量启动任务

    Args:
        task_ids: 任务ID列表
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含批量启动结果的响应对象

    Raises:
        HTTPException: 启动失败时抛出
    """
    try:
        results = await TaskService.batch_start_tasks(db, task_ids)

        # 添加后台任务
        if background_tasks:
            for task_id, result in zip(task_ids, results):
                background_tasks.add_task(TaskService.monitor_task_execution, task_id, result)

        return Response(code=200, message="批量启动任务成功", data=results)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量启动任务失败: {str(e)}")


@router.router.post(
    "/schedule", response_model=Response[Dict[str, Any]], summary="设置任务调度", description="设置任务的调度规则"
)
@requires_permissions(["manage_task_schedules"])
async def set_task_schedule(
    task_id: int = Query(..., description="任务ID"),
    schedule: Dict[str, Any] = Body(..., description="调度规则"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """设置任务调度

    Args:
        task_id: 任务ID
        schedule: 调度规则配置
        db: 数据库会话

    Returns:
        包含调度设置结果的响应对象

    Raises:
        HTTPException: 设置失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        result = await TaskService.set_task_schedule(db, task_id, schedule)
        return Response(code=200, message="设置任务调度成功", data=result)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"设置任务调度失败: {str(e)}")


@router.router.get(
    "/dependencies",
    response_model=Response[Dict[str, Any]],
    summary="获取任务依赖",
    description="获取指定任务的依赖关系",
)
@requires_permissions(["view_task_dependencies"])
async def get_task_dependencies(
    task_id: int = Query(..., description="任务ID"),
    depth: int = Query(1, ge=1, le=5, description="依赖深度"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取任务依赖

    Args:
        task_id: 任务ID
        depth: 依赖关系深度
        db: 数据库会话

    Returns:
        包含任务依赖关系的响应对象

    Raises:
        HTTPException: 查询失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        dependencies = await TaskService.get_task_dependencies(db, task_id=task_id, depth=depth)
        return Response(code=200, message="获取任务依赖成功", data=dependencies)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取任务依赖失败: {str(e)}")


@router.router.post(
    "/retry", response_model=Response[Dict[str, Any]], summary="重试失败任务", description="重试执行失败的任务"
)
@requires_permissions(["manage_tasks"])
async def retry_failed_task(
    task_id: int = Query(..., description="任务ID"),
    max_retries: int = Query(3, ge=1, le=10, description="最大重试次数"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """重试失败任务

    Args:
        task_id: 任务ID
        max_retries: 最大重试次数
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含重试结果的响应对象

    Raises:
        HTTPException: 重试失败时抛出
        NotFoundException: 任务不存在时抛出
    """
    try:
        result = await TaskService.retry_failed_task(db, task_id=task_id, max_retries=max_retries)

        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(TaskService.monitor_task_execution, task_id, result)

        return Response(code=200, message="重试失败任务成功", data=result)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重试失败任务失败: {str(e)}",
        )
