# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：students.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：学生管理模块

提供学生信息管理、班级管理、年级管理、专业管理等功能
支持缓存、权限控制和数据验证
"""
from typing import List, Optional, Dict, Any

from fastapi import Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session

from api.base.crud import CRUDRouter
from core.cache.config.config import CacheConfig
from core.dependencies import async_db
from core.dependencies.permissions import requires_permissions
from models.student import Student
from schemas import ClassResponse, GradeResponse, MajorResponse, DepartmentResponse
from schemas.base.response import Response
from schemas.student import (
    StudentCreate,
    StudentFilter,
    StudentResponse,
    StudentUpdate,
)
from services.academic.student.student import StudentService

# 缓存配置
STUDENT_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "student:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 3600,  # 缓存1小时
}

router = CRUDRouter[Student, StudentCreate, StudentUpdate, StudentFilter, StudentResponse](
    schema=StudentResponse,
    create_schema=StudentCreate,
    update_schema=StudentUpdate,
    filter_schema=StudentFilter,
    service=StudentService(),
    prefix="/students",
    tags=["学生管理"],
    cache_config=STUDENT_CACHE_CONFIG,
)


@router.router.get(
    "/classes",
    response_model=Response[List[ClassResponse]],
    summary="获取班级列表",
    description="获取系统中所有的班级信息列表，支持分页和过滤",
)
@requires_permissions(["view_classes"])
async def get_classes(
    db: Session = Depends(async_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    grade_id: Optional[int] = Query(None, description="年级ID过滤"),
    major_id: Optional[int] = Query(None, description="专业ID过滤"),
    department_id: Optional[int] = Query(None, description="院系ID过滤"),
) -> Response[List[ClassResponse]]:
    """获取班级列表

    Args:
        db: 数据库会话
        page: 页码，从1开始
        page_size: 每页记录数
        grade_id: 可选的年级ID过滤
        major_id: 可选的专业ID过滤
        department_id: 可选的院系ID过滤

    Returns:
        包含班级列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        classes = await StudentService().get_classes(
            db,
            skip=(page - 1) * page_size,
            limit=page_size,
            grade_id=grade_id,
            major_id=major_id,
            department_id=department_id,
        )
        return Response(code=200, message="获取班级列表成功", data=classes)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取班级列表失败: {str(e)}")


@router.router.get(
    "/grades",
    response_model=Response[List[GradeResponse]],
    summary="获取年级列表",
    description="获取系统中所有的年级信息列表，支持分页和过滤",
)
@requires_permissions(["view_grades"])
async def get_grades(
    db: Session = Depends(async_db), department_id: Optional[int] = Query(None, description="院系ID过滤")
) -> Response[List[GradeResponse]]:
    """获取年级列表

    Args:
        db: 数据库会话
        department_id: 可选的院系ID过滤

    Returns:
        包含年级列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        grades = await StudentService().get_grades(db, department_id=department_id)
        return Response(code=200, message="获取年级列表成功", data=grades)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取年级列表失败: {str(e)}")


@router.router.get(
    "/majors",
    response_model=Response[List[MajorResponse]],
    summary="获取专业列表",
    description="获取系统中所有的专业信息列表，支持分页和过滤",
)
@requires_permissions(["view_majors"])
async def get_majors(
    db: Session = Depends(async_db),
    department_id: Optional[int] = Query(None, description="院系ID过滤"),
    grade_id: Optional[int] = Query(None, description="年级ID过滤"),
) -> Response[List[MajorResponse]]:
    """获取专业列表

    Args:
        db: 数据库会话
        department_id: 可选的院系ID过滤
        grade_id: 可选的年级ID过滤

    Returns:
        包含专业列表的响应对象

    Raises:
        HTTPException: 数据库查询异常时抛出
    """
    try:
        majors = await StudentService().get_majors(db, department_id=department_id, grade_id=grade_id)
        return Response(code=200, message="获取专业列表成功", data=majors)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取专业列表失败: {str(e)}")


@router.router.get(
    "/departments",
    response_model=Response[List[DepartmentResponse]],
    summary="获取院系列表",
    description="获取系统中所有的院系信息列表，支持分页",
)
@requires_permissions(["view_departments"])
async def get_departments(
    db: Session = Depends(async_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Response[List[DepartmentResponse]]:
    """获取院系列表

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
        departments = await StudentService().get_departments(db, skip=(page - 1) * page_size, limit=page_size)
        return Response(code=200, message="获取院系列表成功", data=departments)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取院系列表失败: {str(e)}")


# 新增API端点
@router.router.get(
    "/{student_id}/statistics",
    response_model=Response[Dict[str, Any]],
    summary="获取学生统计信息",
    description="获取指定学生的统计信息，包括课程数、成绩统计等",
)
@requires_permissions(["view_student_statistics"])
async def get_student_statistics(
    student_id: int = Path(..., description="学生ID"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """获取学生统计信息

    Args:
        student_id: 学生ID
        db: 数据库会话

    Returns:
        包含学生统计信息的响应对象

    Raises:
        HTTPException: 未找到学生或查询异常时抛出
    """
    try:
        stats = await StudentService().get_student_statistics(db, student_id)
        return Response(code=200, message="获取学生统计信息成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取学生统计信息失败: {str(e)}")


@router.router.get(
    "/{student_id}/courses",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取学生课程信息",
    description="获取指定学生的选课信息，包括已选课程、成绩等",
)
@requires_permissions(["view_student_courses"])
async def get_student_courses(
    student_id: int = Path(..., description="学生ID"),
    semester: Optional[str] = Query(None, description="学期"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取学生课程信息

    Args:
        student_id: 学生ID
        semester: 可选的学期过滤
        db: 数据库会话

    Returns:
        包含学生课程信息的响应对象

    Raises:
        HTTPException: 未找到学生或查询异常时抛出
    """
    try:
        courses = await StudentService().get_student_courses(db, student_id, semester=semester)
        return Response(code=200, message="获取学生课程信息成功", data=courses)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取学生课程信息失败: {str(e)}")


@router.router.get(
    "/{student_id}/attendance",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取学生考勤信息",
    description="获取指定学生的考勤记录",
)
@requires_permissions(["view_student_attendance"])
async def get_student_attendance(
    student_id: int = Path(..., description="学生ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    course_id: Optional[int] = Query(None, description="课程ID"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取学生考勤信息

    Args:
        student_id: 学生ID
        start_date: 可选的开始日期
        end_date: 可选的结束日期
        course_id: 可选的课程ID
        db: 数据库会话

    Returns:
        包含学生考勤信息的响应对象

    Raises:
        HTTPException: 未找到学生或查询异常时抛出
    """
    try:
        attendance = await StudentService().get_student_attendance(
            db, student_id, start_date=start_date, end_date=end_date, course_id=course_id
        )
        return Response(code=200, message="获取学生考勤信息成功", data=attendance)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取学生考勤信息失败: {str(e)}")
