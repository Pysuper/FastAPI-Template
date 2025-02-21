# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：stats.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：统计分析模块

提供系统各模块的统计分析功能
支持多维度数据统计和趋势分析
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from core.cache.config.config import CacheConfig
from core.dependencies.permissions import requires_permissions
from core.dependencies.auth import get_current_user, get_db
from schemas.common import Response
from services.stats.stats_service import StatsService

# 缓存配置
STATS_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "stats:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 3600,  # 缓存1小时
}

router = APIRouter(prefix="/stats", tags=["统计分析"])


@router.get(
    "/overview",
    response_model=Response[Dict[str, Any]],
    summary="获取概览统计",
    description="获取系统整体运行情况的统计概览",
)
@requires_permissions(["view_stats_overview"])
async def get_overview_stats(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取概览统计

    Args:
        start_date: 可选的开始日期
        end_date: 可选的结束日期
        db: 数据库会话

    Returns:
        包含统计概览信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_overview_stats(db, start_date=start_date, end_date=end_date)
        return Response(code=200, message="获取统计概览成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取统计概览失败: {str(e)}")


@router.get(
    "/users", response_model=Response[Dict[str, Any]], summary="获取用户统计", description="获取用户相关的统计数据"
)
@requires_permissions(["view_user_stats"])
async def get_user_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    user_type: Optional[str] = Query(None, description="用户类型"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取用户统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        user_type: 可选的用户类型过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含用户统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_user_stats(
            db, start_time=start_time, end_time=end_time, user_type=user_type, group_by=group_by
        )
        return Response(code=200, message="获取用户统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取用户统计失败: {str(e)}")


@router.get(
    "/students", response_model=Response[Dict[str, Any]], summary="获取学生统计", description="获取学生相关的统计数据"
)
@requires_permissions(["view_student_stats"])
async def get_student_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    grade: Optional[str] = Query(None, description="年级"),
    major: Optional[str] = Query(None, description="专业"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取学生统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        grade: 可选的年级过滤
        major: 可选的专业过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含学生统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_student_stats(
            db, start_time=start_time, end_time=end_time, grade=grade, major=major, group_by=group_by
        )
        return Response(code=200, message="获取学生统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取学生统计失败: {str(e)}")


@router.get(
    "/teachers", response_model=Response[Dict[str, Any]], summary="获取教师统计", description="获取教师相关的统计数据"
)
@requires_permissions(["view_teacher_stats"])
async def get_teacher_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    department: Optional[str] = Query(None, description="院系"),
    title: Optional[str] = Query(None, description="职称"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取教师统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        department: 可选的院系过滤
        title: 可选的职称过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含教师统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_teacher_stats(
            db, start_time=start_time, end_time=end_time, department=department, title=title, group_by=group_by
        )
        return Response(code=200, message="获取教师统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取教师统计失败: {str(e)}")


@router.get(
    "/courses", response_model=Response[Dict[str, Any]], summary="获取课程统计", description="获取课程相关的统计数据"
)
@requires_permissions(["view_course_stats"])
async def get_course_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    course_type: Optional[str] = Query(None, description="课程类型"),
    department: Optional[str] = Query(None, description="开课院系"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取课程统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        course_type: 可选的课程类型过滤
        department: 可选的开课院系过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含课程统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_course_stats(
            db,
            start_time=start_time,
            end_time=end_time,
            course_type=course_type,
            department=department,
            group_by=group_by,
        )
        return Response(code=200, message="获取课程统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取课程统计失败: {str(e)}")


@router.get(
    "/exams", response_model=Response[Dict[str, Any]], summary="获取考试统计", description="获取考试相关的统计数据"
)
@requires_permissions(["view_exam_stats"])
async def get_exam_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    exam_type: Optional[str] = Query(None, description="考试类型"),
    course_id: Optional[int] = Query(None, description="课程ID"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取考试统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        exam_type: 可选的考试类型过滤
        course_id: 可选的课程ID过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含考试统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_exam_stats(
            db, start_time=start_time, end_time=end_time, exam_type=exam_type, course_id=course_id, group_by=group_by
        )
        return Response(code=200, message="获取考试统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取考试统计失败: {str(e)}")


@router.get(
    "/evaluations",
    response_model=Response[Dict[str, Any]],
    summary="获取评教统计",
    description="获取评教相关的统计数据",
)
@requires_permissions(["view_evaluation_stats"])
async def get_evaluation_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    course_id: Optional[int] = Query(None, description="课程ID"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取评教统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        teacher_id: 可选的教师ID过滤
        course_id: 可选的课程ID过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含评教统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_evaluation_stats(
            db, start_time=start_time, end_time=end_time, teacher_id=teacher_id, course_id=course_id, group_by=group_by
        )
        return Response(code=200, message="获取评教统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取评教统计失败: {str(e)}")


@router.get(
    "/files", response_model=Response[Dict[str, Any]], summary="获取文件统计", description="获取文件相关的统计数据"
)
@requires_permissions(["view_file_stats"])
async def get_file_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    file_type: Optional[str] = Query(None, description="文件类型"),
    folder_id: Optional[int] = Query(None, description="文件夹ID"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取文件统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        file_type: 可选的文件类型过滤
        folder_id: 可选的文件夹ID过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含文件统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_file_stats(
            db, start_time=start_time, end_time=end_time, file_type=file_type, folder_id=folder_id, group_by=group_by
        )
        return Response(code=200, message="获取文件统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取文件统计失败: {str(e)}")


@router.get(
    "/messages", response_model=Response[Dict[str, Any]], summary="获取消息统计", description="获取消息相关的统计数据"
)
@requires_permissions(["view_message_stats"])
async def get_message_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    message_type: Optional[str] = Query(None, description="消息类型"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取消息统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        message_type: 可选的消息类型过滤
        user_id: 可选的用户ID过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含消息统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_message_stats(
            db, start_time=start_time, end_time=end_time, message_type=message_type, user_id=user_id, group_by=group_by
        )
        return Response(code=200, message="获取消息统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取消息统计失败: {str(e)}")


@router.get(
    "/notifications",
    response_model=Response[Dict[str, Any]],
    summary="获取通知统计",
    description="获取通知相关的统计数据",
)
@requires_permissions(["view_notification_stats"])
async def get_notification_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    notification_type: Optional[str] = Query(None, description="通知类型"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取通知统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        notification_type: 可选的通知类型过滤
        user_id: 可选的用户ID过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含通知统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_notification_stats(
            db,
            start_time=start_time,
            end_time=end_time,
            notification_type=notification_type,
            user_id=user_id,
            group_by=group_by,
        )
        return Response(code=200, message="获取通知统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取通知统计失败: {str(e)}")


@router.get(
    "/logs", response_model=Response[Dict[str, Any]], summary="获取日志统计", description="获取日志相关的统计数据"
)
@requires_permissions(["view_log_stats"])
async def get_log_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    log_level: Optional[str] = Query(None, description="日志级别"),
    module: Optional[str] = Query(None, description="模块名称"),
    group_by: Optional[str] = Query(None, description="分组方式"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取日志统计

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        log_level: 可选的日志级别过滤
        module: 可选的模块名称过滤
        group_by: 可选的分组方式
        db: 数据库会话

    Returns:
        包含日志统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await StatsService.get_log_stats(
            db, start_time=start_time, end_time=end_time, log_level=log_level, module=module, group_by=group_by
        )
        return Response(code=200, message="获取日志统计成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取日志统计失败: {str(e)}")


# 新增API端点
@router.get(
    "/trends", response_model=Response[Dict[str, Any]], summary="获取趋势分析", description="获取各类数据的趋势分析"
)
@requires_permissions(["view_trend_stats"])
async def get_trend_stats(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    metric: str = Query(..., description="统计指标"),
    interval: str = Query("day", description="统计间隔"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取趋势分析

    Args:
        start_time: 可选的开始时间
        end_time: 可选的结束时间
        metric: 统计指标
        interval: 统计间隔(day/week/month/year)
        db: 数据库会话

    Returns:
        包含趋势分析数据的响应对象

    Raises:
        HTTPException: 分析失败时抛出
    """
    try:
        trends = await StatsService.get_trend_stats(
            db, start_time=start_time, end_time=end_time, metric=metric, interval=interval
        )
        return Response(code=200, message="获取趋势分析成功", data=trends)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取趋势分析失败: {str(e)}")


@router.get(
    "/compare",
    response_model=Response[Dict[str, Any]],
    summary="获取对比分析",
    description="获取不同维度的数据对比分析",
)
@requires_permissions(["view_compare_stats"])
async def get_compare_stats(
    dimension: str = Query(..., description="对比维度"),
    metrics: List[str] = Query(..., description="统计指标列表"),
    filters: Optional[Dict[str, Any]] = Query(None, description="过滤条件"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取对比分析

    Args:
        dimension: 对比维度
        metrics: 统计指标列表
        filters: 可选的过滤条件
        db: 数据库会话

    Returns:
        包含对比分析数据的响应对象

    Raises:
        HTTPException: 分析失败时抛出
    """
    try:
        comparison = await StatsService.get_compare_stats(db, dimension=dimension, metrics=metrics, filters=filters)
        return Response(code=200, message="获取对比分析成功", data=comparison)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取对比分析失败: {str(e)}")


@router.get(
    "/rankings",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取排名统计",
    description="获取各类数据的排名统计",
)
@requires_permissions(["view_ranking_stats"])
async def get_ranking_stats(
    metric: str = Query(..., description="统计指标"),
    dimension: str = Query(..., description="排名维度"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    filters: Optional[Dict[str, Any]] = Query(None, description="过滤条件"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取排名统计

    Args:
        metric: 统计指标
        dimension: 排名维度
        limit: 返回数量
        filters: 可选的过滤条件
        db: 数据库会话

    Returns:
        包含排名统计数据的响应对象

    Raises:
        HTTPException: 统计失败时抛出
    """
    try:
        rankings = await StatsService.get_ranking_stats(
            db, metric=metric, dimension=dimension, limit=limit, filters=filters
        )
        return Response(code=200, message="获取排名统计成功", data=rankings)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取排名统计失败: {str(e)}")
