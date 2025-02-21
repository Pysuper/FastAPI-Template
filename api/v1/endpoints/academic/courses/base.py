from core.schemas.common import PageResponse, Response
from dependencies.auth import get_current_active_user
from dependencies.db import get_db
from exceptions.system.database import NotFoundException
from fastapi import APIRouter, Body, Depends, File, Path, Query, UploadFile
from schemas.auth import User
from sqlalchemy.orm import Session

from schemas.course import (
    CourseCreate,
    CourseDepartmentUpdate,
    CourseResponse,
    CourseStatusUpdate,
    CourseTypeUpdate,
    CourseUpdate,
)
from services.academic.teaching.course import CourseService

router = APIRouter(prefix="/courses", tags=["课程"])


@router.get("/", response_model=PageResponse[CourseResponse], summary="获取课程列表")
async def get_courses(
    query: str = Query(None, description="搜索关键词"),
    status: str = Query(None, description="状态"),
    type: str = Query(None, description="类型"),
    category: str = Query(None, description="分类"),
    department_id: int = Query(None, description="院系ID"),
    teacher_id: int = Query(None, description="教师ID"),
    semester: str = Query(None, description="学期"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query(None, description="排序字段"),
    order: str = Query("desc", description="排序方向"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取课程列表"""
    service = CourseService(db)
    total, items = service.get_courses(
        query=query,
        status=status,
        type=type,
        category=category,
        department_id=department_id,
        teacher_id=teacher_id,
        semester=semester,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
        sort=sort,
        order=order,
    )
    return PageResponse(total=total, items=items, page=page, size=size)


@router.post("/", response_model=Response, summary="创建课程")
async def create_course(
    data: CourseCreate, db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)
):
    """创建课程"""
    service = CourseService(db)
    course = service.create_course(data)
    return Response(data={"id": course.id})


@router.get("/{id}", response_model=Response, summary="获取课程详情")
async def get_course(
    id: int = Path(..., description="课程ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取课程详情"""
    service = CourseService(db)
    course = service.get_course(id)
    if not course:
        raise NotFoundException("课程不存在")
    return Response(data=course)


@router.put("/{id}", response_model=Response, summary="更新课程")
async def update_course(
    id: int = Path(..., description="课程ID"),
    data: CourseUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新课程"""
    service = CourseService(db)
    course = service.update_course(id, data)
    return Response()


@router.delete("/{id}", response_model=Response, summary="删除课程")
async def delete_course(
    id: int = Path(..., description="课程ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除课程"""
    service = CourseService(db)
    service.delete_course(id)
    return Response()


@router.put("/{id}/status", response_model=Response, summary="更新课程状态")
async def update_course_status(
    id: int = Path(..., description="课程ID"),
    data: CourseStatusUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新课程状态"""
    service = CourseService(db)
    service.update_course_status(id, data.status)
    return Response()


@router.put("/{id}/type", response_model=Response, summary="更新课程类型")
async def update_course_type(
    id: int = Path(..., description="课程ID"),
    data: CourseTypeUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新课程类型"""
    service = CourseService(db)
    service.update_course_type(id, data.type)
    return Response()


@router.put("/{id}/department", response_model=Response, summary="更新课程院系")
async def update_course_department(
    id: int = Path(..., description="课程ID"),
    data: CourseDepartmentUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新课程院系"""
    service = CourseService(db)
    service.update_course_department(id, data.department_id)
    return Response()


@router.get("/types", response_model=Response, summary="获取课程类型列表")
async def get_types(db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)):
    """获取课程类型列表"""
    service = CourseService(db)
    types = service.get_types()
    return Response(data=types)


@router.get("/categories", response_model=Response, summary="获取课程分类列表")
async def get_categories(db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)):
    """获取课程分类列表"""
    service = CourseService(db)
    categories = service.get_categories()
    return Response(data=categories)


@router.post("/import", response_model=Response, summary="导入课程")
async def import_courses(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)
):
    """导入课程"""
    service = CourseService(db)
    result = service.import_courses(file)
    return Response(data=result)


@router.get("/export", response_model=Response, summary="导出课程")
async def export_courses(
    query: str = Query(None, description="搜索关键词"),
    status: str = Query(None, description="状态"),
    type: str = Query(None, description="类型"),
    category: str = Query(None, description="分类"),
    department_id: int = Query(None, description="院系ID"),
    teacher_id: int = Query(None, description="教师ID"),
    semester: str = Query(None, description="学期"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导出课程"""
    service = CourseService(db)
    result = service.export_courses(
        query=query,
        status=status,
        type=type,
        category=category,
        department_id=department_id,
        teacher_id=teacher_id,
        semester=semester,
    )
    return Response(data=result)


@router.get("/stats", response_model=Response, summary="获取课程统计")
async def get_course_stats(
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取课程统计"""
    service = CourseService(db)
    stats = service.get_course_stats(start_time=start_time, end_time=end_time)
    return Response(data=stats)
