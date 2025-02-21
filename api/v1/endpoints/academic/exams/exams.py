# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：exams.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：考试管理模块

提供考试信息管理、考场管理、考试安排、成绩管理等功能
支持缓存、权限控制和数据验证
"""
from typing import List, Optional, Dict, Any

from core.dependencies.permissions import requires_permissions
from fastapi import Body, Depends, Path, Query, HTTPException, status
from services.academic.exam.exam import ExamService
from sqlalchemy.orm import Session

from api.base.crud import CRUDRouter
from core.cache.config.config import CacheConfig
from core.dependencies import async_db
from models.exam import Exam
from schemas.base.response import Response
from schemas.exam import (
    ExamCreate,
    ExamFilter,
    ExamUpdate,
    ExamTypeResponse,
    ExamRoomResponse,
    ExamScheduleResponse,
    ExamScoreResponse,
    ExamScheduleCreate,
    ExamScheduleUpdate,
    ExamScoreCreate,
    ExamScoreUpdate,
)

# 缓存配置
EXAM_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "exam:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 3600,  # 缓存1小时
}

router = CRUDRouter(
    model=Exam,
    create_schema=ExamCreate,
    update_schema=ExamUpdate,
    filter_schema=ExamFilter,
    prefix="/exams",
    tags=["考试管理"],
    cache_config=EXAM_CACHE_CONFIG,
)


@router.router.get(
    "/types",
    response_model=Response[List[ExamTypeResponse]],
    summary="获取考试类型列表",
    description="获取所有可用的考试类型列表",
)
@requires_permissions(["view_exam_types"])
async def get_types(db: Session = Depends(async_db)) -> Response[List[ExamTypeResponse]]:
    """获取考试类型列表

    Args:
        db: 数据库会话

    Returns:
        包含考试类型列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        types = await ExamService().get_exam_types(db)
        return Response(code=200, message="获取考试类型列表成功", data=types)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取考试类型列表失败: {str(e)}")


@router.router.get(
    "/rooms",
    response_model=Response[List[ExamRoomResponse]],
    summary="获取考场列表",
    description="获取所有可用的考场信息列表，支持分页和过滤",
)
@requires_permissions(["view_exam_rooms"])
async def get_rooms(
    db: Session = Depends(async_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    building: Optional[str] = Query(None, description="教学楼"),
    capacity: Optional[int] = Query(None, ge=0, description="最小容量"),
    is_available: Optional[bool] = Query(None, description="是否可用"),
) -> Response[List[ExamRoomResponse]]:
    """获取考场列表

    Args:
        db: 数据库会话
        page: 页码，从1开始
        page_size: 每页记录数
        building: 可选的教学楼过滤
        capacity: 可选的最小容量过滤
        is_available: 可选的可用状态过滤

    Returns:
        包含考场列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        rooms = await ExamService().get_exam_rooms(
            db,
            skip=(page - 1) * page_size,
            limit=page_size,
            building=building,
            capacity=capacity,
            is_available=is_available,
        )
        return Response(code=200, message="获取考场列表成功", data=rooms)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取考场列表失败: {str(e)}",
        )


@router.router.get(
    "/schedules",
    response_model=Response[List[ExamScheduleResponse]],
    summary="获取考试安排列表",
    description="获取指定考试的考试安排列表，支持分页和过滤",
)
@requires_permissions(["view_exam_schedules"])
async def get_schedules(
    exam_id: int = Query(..., description="考试ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    room_id: Optional[int] = Query(None, description="考场ID"),
    date: Optional[str] = Query(None, description="考试日期"),
    db: Session = Depends(async_db),
) -> Response[List[ExamScheduleResponse]]:
    """获取考试安排列表

    Args:
        exam_id: 考试ID
        page: 页码，从1开始
        page_size: 每页记录数
        room_id: 可选的考场ID过滤
        date: 可选的考试日期过滤
        db: 数据库会话

    Returns:
        包含考试安排列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        schedules = await ExamService().get_exam_schedules(
            db,
            exam_id,
            skip=(page - 1) * page_size,
            limit=page_size,
            room_id=room_id,
            date=date,
        )
        return Response(code=200, message="获取考试安排列表成功", data=schedules)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取考试安排列表失败: {str(e)}",
        )


@router.router.post(
    "/schedules",
    response_model=Response[ExamScheduleResponse],
    summary="创建考试安排",
    description="为指定考试创建新的考试安排",
)
@requires_permissions(["create_exam_schedule"])
async def create_schedule(
    exam_id: int = Query(..., description="考试ID"),
    data: ExamScheduleCreate = Body(..., description="考试安排数据"),
    db: Session = Depends(async_db),
) -> Response[ExamScheduleResponse]:
    """创建考试安排

    Args:
        exam_id: 考试ID
        data: 考试安排创建数据
        db: 数据库会话

    Returns:
        包含新创建的考试安排的响应对象

    Raises:
        HTTPException: 创建失败时抛出
    """
    try:
        schedule = await ExamService().create_exam_schedule(db, exam_id, data)
        return Response(code=201, message="创建考试安排成功", data=schedule)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建考试安排失败: {str(e)}",
        )


@router.router.put(
    "/schedules/{schedule_id}",
    response_model=Response[ExamScheduleResponse],
    summary="更新考试安排",
    description="更新指定的考试安排信息",
)
@requires_permissions(["update_exam_schedule"])
async def update_schedule(
    schedule_id: int = Path(..., description="考试安排ID"),
    data: ExamScheduleUpdate = Body(..., description="考试安排更新数据"),
    db: Session = Depends(async_db),
) -> Response[ExamScheduleResponse]:
    """更新考试安排

    Args:
        schedule_id: 考试安排ID
        data: 考试安排更新数据
        db: 数据库会话

    Returns:
        包含更新后的考试安排的响应对象

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        schedule = await ExamService().update_exam_schedule(db, schedule_id, data)
        return Response(code=200, message="更新考试安排成功", data=schedule)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新考试安排失败: {str(e)}",
        )


@router.router.delete(
    "/schedules/{schedule_id}",
    response_model=Response,
    summary="删除考试安排",
    description="删除指定的考试安排",
)
@requires_permissions(["delete_exam_schedule"])
async def delete_schedule(
    schedule_id: int = Path(..., description="考试安排ID"), db: Session = Depends(async_db)
) -> Response:
    """删除考试安排

    Args:
        schedule_id: 考试安排ID
        db: 数据库会话

    Returns:
        删除操作的响应对象

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        await ExamService().delete_exam_schedule(db, schedule_id)
        return Response(code=200, message="删除考试安排成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除考试安排失败: {str(e)}")


@router.router.get(
    "/scores",
    response_model=Response[List[ExamScoreResponse]],
    summary="获取考试成绩列表",
    description="获取指定考试的成绩列表，支持分页和过滤",
)
@requires_permissions(["view_exam_scores"])
async def get_scores(
    exam_id: int = Query(..., description="考试ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    student_id: Optional[int] = Query(None, description="学生ID"),
    min_score: Optional[float] = Query(None, ge=0, description="最低分数"),
    max_score: Optional[float] = Query(None, le=100, description="最高分数"),
    db: Session = Depends(async_db),
) -> Response[List[ExamScoreResponse]]:
    """获取考试成绩列表

    Args:
        exam_id: 考试ID
        page: 页码，从1开始
        page_size: 每页记录数
        student_id: 可选的学生ID过滤
        min_score: 可选的最低分数过滤
        max_score: 可选的最高分数过滤
        db: 数据库会话

    Returns:
        包含考试成绩列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        scores = await ExamService().get_exam_scores(
            db,
            exam_id,
            skip=(page - 1) * page_size,
            limit=page_size,
            student_id=student_id,
            min_score=min_score,
            max_score=max_score,
        )
        return Response(code=200, message="获取考试成绩列表成功", data=scores)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取考试成绩列表失败: {str(e)}",
        )


@router.router.post(
    "/scores",
    response_model=Response[ExamScoreResponse],
    summary="录入考试成绩",
    description="为指定考试录入学生成绩",
)
@requires_permissions(["create_exam_score"])
async def create_score(
    exam_id: int = Query(..., description="考试ID"),
    data: ExamScoreCreate = Body(..., description="考试成绩数据"),
    db: Session = Depends(async_db),
) -> Response[ExamScoreResponse]:
    """录入考试成绩

    Args:
        exam_id: 考试ID
        data: 考试成绩创建数据
        db: 数据库会话

    Returns:
        包含新录入的考试成绩的响应对象

    Raises:
        HTTPException: 录入失败时抛出
    """
    try:
        score = await ExamService().create_exam_score(db, exam_id, data)
        return Response(code=201, message="录入考试成绩成功", data=score)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"录入考试成绩失败: {str(e)}",
        )


@router.router.put(
    "/scores/{score_id}",
    response_model=Response[ExamScoreResponse],
    summary="更新考试成绩",
    description="更新指定的考试成绩信息",
)
@requires_permissions(["update_exam_score"])
async def update_score(
    score_id: int = Path(..., description="考试成绩ID"),
    data: ExamScoreUpdate = Body(..., description="考试成绩更新数据"),
    db: Session = Depends(async_db),
) -> Response[ExamScoreResponse]:
    """更新考试成绩

    Args:
        score_id: 考试成绩ID
        data: 考试成绩更新数据
        db: 数据库会话

    Returns:
        包含更新后的考试成绩的响应对象

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        score = await ExamService().update_exam_score(db, score_id, data)
        return Response(code=200, message="更新考试成绩成功", data=score)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新考试成绩失败: {str(e)}",
        )


@router.router.delete(
    "/scores/{score_id}",
    response_model=Response,
    summary="删除考试成绩",
    description="删除指定的考试成绩",
)
@requires_permissions(["delete_exam_score"])
async def delete_score(
    score_id: int = Path(..., description="考试成绩ID"), db: Session = Depends(async_db)
) -> Response:
    """删除考试成绩

    Args:
        score_id: 考试成绩ID
        db: 数据库会话

    Returns:
        删除操作的响应对象

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        await ExamService().delete_exam_score(db, score_id)
        return Response(code=200, message="删除考试成绩成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除考试成绩失败: {str(e)}",
        )


# 新增API端点
@router.router.get(
    "/{exam_id}/statistics",
    response_model=Response[Dict[str, Any]],
    summary="获取考试统计信息",
    description="获取指定考试的统计信息，包括参考人数、平均分、及格率等",
)
@requires_permissions(["view_exam_statistics"])
async def get_exam_statistics(
    exam_id: int = Path(..., description="考试ID"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """获取考试统计信息

    Args:
        exam_id: 考试ID
        db: 数据库会话

    Returns:
        包含考试统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await ExamService().get_exam_statistics(db, exam_id)
        return Response(code=200, message="获取考试统计信息成功", data=stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取考试统计信息失败: {str(e)}",
        )


@router.router.post(
    "/batch-scores",
    response_model=Response[List[ExamScoreResponse]],
    summary="批量录入考试成绩",
    description="批量录入多个学生的考试成绩",
)
@requires_permissions(["create_exam_scores"])
async def create_batch_scores(
    exam_id: int = Query(..., description="考试ID"),
    data: List[ExamScoreCreate] = Body(..., description="考试成绩数据列表"),
    db: Session = Depends(async_db),
) -> Response[List[ExamScoreResponse]]:
    """批量录入考试成绩

    Args:
        exam_id: 考试ID
        data: 考试成绩创建数据列表
        db: 数据库会话

    Returns:
        包含新录入的考试成绩列表的响应对象

    Raises:
        HTTPException: 录入失败时抛出
    """
    try:
        scores = await ExamService().create_batch_exam_scores(db, exam_id, data)
        return Response(code=201, message="批量录入考试成绩成功", data=scores)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量录入考试成绩失败: {str(e)}",
        )
