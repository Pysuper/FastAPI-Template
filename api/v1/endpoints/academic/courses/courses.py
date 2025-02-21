# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：courses.py
@Author  ：PySuper
@Date    ：2024/12/20 14:45 
@Desc    ：Speedy courses.py
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status, Path, Body
from sqlalchemy.orm import Session

from api.base.crud import CRUDRouter
from cache import Cache
from core.config.settings import logger
from core.constants.enums import ResourceType, Action
from core.schemas.common import Response
from dependencies.auth import get_current_active_user
from dependencies.db import get_db
from dependencies.pagination import get_pagination_params
from models.course import Course
from rbac.permissions import PermissionChecker
from schemas.course import CourseResponse, CourseCreate, CourseUpdate, CourseFilter
from schemas.response import PaginatedResponse, PaginationParams
from schemas.validators import ResponseModel
from services.academic.teaching.course import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])
permission = PermissionChecker(get_db(), Cache())
# router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CourseResponse])
async def get_courses(
    *,
    db: Session = Depends(async_db),
    pagination: PaginationParams = Depends(get_pagination_params),
    department_id: int = None,
    teacher_id: int = None,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    获取课程列表
    """
    course_service = CourseService(db)
    courses = course_service.get_courses(
        skip=(pagination.page - 1) * pagination.size,
        limit=pagination.size,
        department_id=department_id,
        teacher_id=teacher_id,
    )
    total = course_service.count_courses(department_id=department_id, teacher_id=teacher_id)
    return {
        "data": courses,
        "total": total,
        "page": pagination.page,
        "size": pagination.size,
        "pages": (total + pagination.size - 1) // pagination.size,
    }


@router.post("/", response_model=CourseResponse)
async def create_course(
    *,
    db: Session = Depends(async_db),
    course_in: CourseCreate,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    创建课程
    """
    course_service = CourseService(db)
    # 检查院系是否存在
    if not course_service.department_exists(course_in.department_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="院系不存在")
    # 检查教师是否存在
    if not course_service.teacher_exists(course_in.teacher_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教师不存在")
    # 检查课程代码是否已存在
    course = course_service.get_course_by_code(course_in.code)
    if course:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程代码已存在")
    course = course_service.create_course(course_in)
    return course


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: Session = Depends(async_db),
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    获取课程信息
    """
    course_service = CourseService(db)
    course = course_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    *,
    db: Session = Depends(async_db),
    course_id: int,
    course_in: CourseUpdate,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    更新课程信息
    """
    course_service = CourseService(db)
    course = course_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    # 如果更新了院系，检查新院系是否存在
    if course_in.department_id and course_in.department_id != course.department_id:
        if not course_service.department_exists(course_in.department_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="院系不存在")
    # 如果更新了教师，检查新教师是否存在
    if course_in.teacher_id and course_in.teacher_id != course.teacher_id:
        if not course_service.teacher_exists(course_in.teacher_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教师不存在")
    # 如果更新了课程代码，检查新代码是否已存在
    if course_in.code and course_in.code != course.code:
        existing_course = course_service.get_course_by_code(course_in.code)
        if existing_course:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程代码已存在")
    course = course_service.update_course(course, course_in)
    return course


@router.delete("/{course_id}")
async def delete_course(
    *,
    db: Session = Depends(async_db),
    course_id: int,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    删除课程
    """
    course_service = CourseService(db)
    course = course_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    # 检查是否有关联的成绩和考勤记录
    if course_service.has_related_records(course_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该课程还有关联的成绩或考勤记录，无法删除")
    course_service.delete_course(course_id)
    return {"msg": "删除成功"}


@router.get("", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.READ)
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    teacher_id: Optional[int] = None,
    db: Session = Depends(async_db),
):
    """获取课程列表"""
    try:
        service = CourseService(db, Cache())
        if teacher_id:
            courses = await service.get_teacher_courses(teacher_id)
        else:
            courses = await service.get_courses(skip, limit)
        return ResponseModel(data={"courses": [course.__dict__ for course in courses]})
    except Exception as e:
        logger.error(f"Failed to get courses: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程列表失败")


@router.get("/{course_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.READ)
async def get_course(course_id: int, db: Session = Depends(async_db)):
    """获取课程详情"""
    try:
        service = CourseService(db, Cache())
        course = await service.get_course_by_id(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        return ResponseModel(data={"course": course.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get course: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程信息失败")


@router.post("", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.CREATE)
async def create_course(course: CourseCreate, db: Session = Depends(async_db)):
    """创建课程"""
    try:
        service = CourseService(db, Cache())
        new_course = await service.create_course(course)
        return ResponseModel(message="创建课程成功", data={"course": new_course.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create course: {str(e)}")
        raise HTTPException(status_code=500, detail="创建课程失败")


@router.put("/{course_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.UPDATE)
async def update_course(course_id: int, course: CourseUpdate, db: Session = Depends(async_db)):
    """更新课程信息"""
    try:
        service = CourseService(db, Cache())
        updated_course = await service.update_course(course_id, course)
        return ResponseModel(message="更新课程成功", data={"course": updated_course.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update course: {str(e)}")
        raise HTTPException(status_code=500, detail="更新课程失败")


@router.delete("/{course_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.DELETE)
async def delete_course(course_id: int, db: Session = Depends(async_db)):
    """删除课程"""
    try:
        service = CourseService(db, Cache())
        await service.delete_course(course_id)
        return ResponseModel(message="删除课程成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to delete course: {str(e)}")
        raise HTTPException(status_code=500, detail="删除课程失败")


@router.get("/{course_id}/materials", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.READ)
async def get_course_materials(
    course_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), db: Session = Depends(async_db)
):
    """获取课程资料列表"""
    try:
        service = CourseService(db, Cache())
        materials = await service.get_course_materials(course_id, skip, limit)
        return ResponseModel(data={"materials": [material.__dict__ for material in materials]})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get course materials: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程资料失败")


@router.post("/{course_id}/materials", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.UPDATE)
async def upload_course_material(
    course_id: int,
    title: str,
    description: Optional[str] = None,
    file: UploadFile = File(...),
    db: Session = Depends(async_db),
):
    """上传课程资料"""
    try:
        service = CourseService(db, Cache())
        material = await service.upload_material(course_id, title, description, file)
        return ResponseModel(message="上传课程资料成功", data={"material": material.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to upload course material: {str(e)}")
        raise HTTPException(status_code=500, detail="上传课程资料失败")


@router.get("/{course_id}/schedule", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.READ)
async def get_course_schedule(course_id: int, db: Session = Depends(async_db)):
    """获取课程安排"""
    try:
        service = CourseService(db, Cache())
        schedule = await service.get_course_schedule(course_id)
        return ResponseModel(data={"schedule": [s.__dict__ for s in schedule]})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get course schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程安排失败")


@router.post("/{course_id}/schedule", response_model=ResponseModel)
@permission.has_permission(ResourceType.COURSE, Action.UPDATE)
async def update_course_schedule(course_id: int, schedules: List[dict], db: Session = Depends(async_db)):
    """更新课程安排"""
    try:
        service = CourseService(db, Cache())
        updated_schedule = await service.update_course_schedule(course_id, schedules)
        return ResponseModel(message="更新课程安排成功", data={"schedule": [s.__dict__ for s in updated_schedule]})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update course schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="更新课程安排失败")


router = CRUDRouter(
    model=Course,
    create_schema=CourseCreate,
    update_schema=CourseUpdate,
    filter_schema=CourseFilter,
    prefix="/courses",
    tags=["课程"],
)


@router.router.get("/types", response_model=Response, summary="获取课程类型列表")
async def get_types(db: Session = Depends(async_db)):
    """获取课程类型列表"""
    return Response(data=[])


@router.router.get("/categories", response_model=Response, summary="获取课程分类列表")
async def get_categories(db: Session = Depends(async_db)):
    """获取课程分类列表"""
    return Response(data=[])


@router.router.get("/schedules", response_model=Response, summary="获取课程安排列表")
async def get_schedules(course_id: int = Query(..., description="课程ID"), db: Session = Depends(async_db)):
    """获取课程安排列表"""

    return Response(data=[])


@router.router.post("/schedules", response_model=Response, summary="创建课程安排")
async def create_schedule(
    course_id: int = Query(..., description="课程ID"),
    data: dict = Body(..., description="课程安排数据"),
    db: Session = Depends(async_db),
):
    """创建课程安排"""

    return Response()


@router.router.put("/schedules/{schedule_id}", response_model=Response, summary="更新课程安排")
async def update_schedule(
    schedule_id: int = Path(..., description="课程安排ID"),
    data: dict = Body(..., description="课程安排数据"),
    db: Session = Depends(async_db),
):
    """更新课程安排"""

    return Response()


@router.router.delete("/schedules/{schedule_id}", response_model=Response, summary="删除课程安排")
async def delete_schedule(schedule_id: int = Path(..., description="课程安排ID"), db: Session = Depends(async_db)):
    """删除课程安排"""

    return Response()
