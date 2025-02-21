# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：teachers.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：Speedy teachers.py
"""
from typing import List, Optional, Dict, Any

from core.dependencies.permissions import requires_permissions
from fastapi import Depends, Query, Path, HTTPException, status
from schemas.subject import SubjectResponse
from sqlalchemy.orm import Session

from api.base.crud import CRUDRouter
from core.cache.config.config import CacheConfig
from core.dependencies import async_db
from schemas.base.response import Response
from schemas.department import DepartmentResponse
from schemas.teacher import TeacherCreate, TeacherFilter, TeacherResponse, TeacherUpdate
from schemas.title import TitleResponse
from services.academic.teaching.teacher import TeacherService

router = CRUDRouter(
    schema=TeacherResponse,
    create_schema=TeacherCreate,
    update_schema=TeacherUpdate,
    filter_schema=TeacherFilter,
    service=TeacherService(),
    prefix="/teachers",
    tags=["教师管理"],
    cache_config={
        "strategy": "redis",
        "prefix": "student:",
        "serializer": "json",
        "settings": CacheConfig,
        "enable_stats": True,
        "enable_memory_cache": True,
        "enable_redis_cache": True,
    },
)


@router.router.get(
    "/departments",
    response_model=Response[List[DepartmentResponse]],
    summary="获取院系列表",
    description="获取所有可用的院系信息列表",
)
@requires_permissions(["view_departments"])
async def get_departments(
    db: Session = Depends(async_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Response[List[DepartmentResponse]]:
    """
    获取院系列表

    Args:
        db: 数据库会话
        page: 页码，从1开始
        page_size: 每页记录数

    Returns:
        包含院系列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        departments = await TeacherService().get_departments(db, skip=(page - 1) * page_size, limit=page_size)
        return Response(code=200, message="获取院系列表成功", data=departments)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取院系列表失败: {str(e)}")


@router.router.get(
    "/titles",
    response_model=Response[List[TitleResponse]],
    summary="获取职称列表",
    description="获取所有教师职称信息列表",
)
@requires_permissions(["view_titles"])
async def get_titles(
    db: Session = Depends(async_db), department_id: Optional[int] = Query(None, description="院系ID过滤")
) -> Response[List[TitleResponse]]:
    """
    获取职称列表

    Args:
        db: 数据库会话
        department_id: 可选的院系ID过滤参数

    Returns:
        包含职称列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        titles = await TeacherService().get_titles(db, department_id=department_id)
        return Response(code=200, message="获取职称列表成功", data=titles)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取职称列表失败: {str(e)}",
        )


@router.router.get(
    "/subjects",
    response_model=Response[List[SubjectResponse]],
    summary="获取学科列表",
    description="获取所有教学学科信息列表",
)
@requires_permissions(["view_subjects"])
async def get_subjects(
    db: Session = Depends(async_db),
    department_id: Optional[int] = Query(None, description="院系ID过滤"),
    title_id: Optional[int] = Query(None, description="职称ID过滤"),
) -> Response[List[SubjectResponse]]:
    """
    获取学科列表

    Args:
        db: 数据库会话
        department_id: 可选的院系ID过滤参数
        title_id: 可选的职称ID过滤参数

    Returns:
        包含学科列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        subjects = await TeacherService().get_subjects(db, department_id=department_id, title_id=title_id)
        return Response(code=200, message="获取学科列表成功", data=subjects)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取学科列表失败: {str(e)}",
        )


# 添加新的API端点
@router.router.get(
    "/{teacher_id}/statistics",
    response_model=Response[Dict[str, Any]],
    summary="获取教师统计信息",
    description="获取指定教师的统计信息，包括课程数、学生数等",
)
@requires_permissions(["view_teacher_statistics"])
async def get_teacher_statistics(
    teacher_id: int = Path(..., description="教师ID"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """
    获取教师统计信息

    Args:
        teacher_id: 教师ID
        db: 数据库会话

    Returns:
        包含教师统计信息的响应对象

    Raises:
        HTTPException: 未找到教师或查询异常时抛出
    """
    try:
        stats = await TeacherService().get_teacher_statistics(db, teacher_id)
        return Response(code=200, message="获取教师统计信息成功", data=stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取教师统计信息失败: {str(e)}",
        )
