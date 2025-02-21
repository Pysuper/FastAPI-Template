from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from core.db import get_db
from core.exceptions import NotFoundException, ValidationException
from core.security import get_current_user, get_current_active_user
from models import User
from models.teacher import Teacher
from schemas.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherFilter,
    TeacherResponse,
    TeacherStatusUpdate,
    TeacherTitleUpdate,
    TeacherDepartmentUpdate,
)
from schemas.common import Response, PageResponse
from services.teacher import TeacherService

router = APIRouter(prefix="/teachers", tags=["教师"])


@router.get("/", response_model=PageResponse[TeacherResponse], summary="获取教师列表")
async def get_teachers(
    query: str = Query(None, description="搜索关键词"),
    status: str = Query(None, description="状态"),
    title: str = Query(None, description="职称"),
    subject: str = Query(None, description="学科"),
    department_id: int = Query(None, description="院系ID"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query(None, description="排序字段"),
    order: str = Query("desc", description="排序方向"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取教师列表"""
    service = TeacherService(db)
    total, items = service.get_teachers(
        query=query,
        status=status,
        title=title,
        subject=subject,
        department_id=department_id,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
        sort=sort,
        order=order,
    )
    return PageResponse(total=total, items=items, page=page, size=size)


@router.post("/", response_model=Response, summary="创建教师")
async def create_teacher(
    data: TeacherCreate, db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)
):
    """创建教师"""
    service = TeacherService(db)
    teacher = service.create_teacher(data)
    return Response(data={"id": teacher.id})


@router.get("/{id}", response_model=Response, summary="获取教师详情")
async def get_teacher(
    id: int = Path(..., description="教师ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取教师详情"""
    service = TeacherService(db)
    teacher = service.get_teacher(id)
    if not teacher:
        raise NotFoundException("教师不存在")
    return Response(data=teacher)


@router.put("/{id}", response_model=Response, summary="更新教师")
async def update_teacher(
    id: int = Path(..., description="教师ID"),
    data: TeacherUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新教师"""
    service = TeacherService(db)
    teacher = service.update_teacher(id, data)
    return Response()


@router.delete("/{id}", response_model=Response, summary="删除教师")
async def delete_teacher(
    id: int = Path(..., description="教师ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除教师"""
    service = TeacherService(db)
    service.delete_teacher(id)
    return Response()


@router.put("/{id}/status", response_model=Response, summary="更新教师状态")
async def update_teacher_status(
    id: int = Path(..., description="教师ID"),
    data: TeacherStatusUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新教师状态"""
    service = TeacherService(db)
    service.update_teacher_status(id, data.status)
    return Response()


@router.put("/{id}/title", response_model=Response, summary="更新教师职称")
async def update_teacher_title(
    id: int = Path(..., description="教师ID"),
    data: TeacherTitleUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新教师职称"""
    service = TeacherService(db)
    service.update_teacher_title(id, data.title)
    return Response()


@router.put("/{id}/department", response_model=Response, summary="更新教师院系")
async def update_teacher_department(
    id: int = Path(..., description="教师ID"),
    data: TeacherDepartmentUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新教师院系"""
    service = TeacherService(db)
    service.update_teacher_department(id, data.department_id)
    return Response()


@router.get("/departments", response_model=Response, summary="获取院系列表")
async def get_departments(db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)):
    """获取院系列表"""
    service = TeacherService(db)
    departments = service.get_departments()
    return Response(data=departments)


@router.get("/titles", response_model=Response, summary="获取职称列表")
async def get_titles(db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)):
    """获取职称列表"""
    service = TeacherService(db)
    titles = service.get_titles()
    return Response(data=titles)


@router.get("/subjects", response_model=Response, summary="获取学科列表")
async def get_subjects(
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取学科列表"""
    service = TeacherService(db)
    subjects = service.get_subjects(department_id)
    return Response(data=subjects)


@router.post("/import", response_model=Response, summary="导入教师")
async def import_teachers(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)
):
    """导入教师"""
    service = TeacherService(db)
    result = service.import_teachers(file)
    return Response(data=result)


@router.get("/export", response_model=Response, summary="导出教师")
async def export_teachers(
    query: str = Query(None, description="搜索关键词"),
    status: str = Query(None, description="状态"),
    title: str = Query(None, description="职称"),
    subject: str = Query(None, description="学科"),
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导出教师"""
    service = TeacherService(db)
    result = service.export_teachers(
        query=query, status=status, title=title, subject=subject, department_id=department_id
    )
    return Response(data=result)


@router.get("/stats", response_model=Response, summary="获取教师统计")
async def get_teacher_stats(
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取教师统计"""
    service = TeacherService(db)
    stats = service.get_teacher_stats(start_time=start_time, end_time=end_time)
    return Response(data=stats)


@router.get("/{id}/courses", response_model=Response, summary="获取教师课程")
async def get_teacher_courses(
    id: int = Path(..., description="教师ID"),
    semester: str = Query(None, description="学期"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取教师课程"""
    service = TeacherService(db)
    courses = service.get_teacher_courses(id, semester)
    return Response(data=courses)


@router.get("/{id}/students", response_model=Response, summary="获取教师学生")
async def get_teacher_students(
    id: int = Path(..., description="教师ID"),
    semester: str = Query(None, description="学期"),
    course_id: int = Query(None, description="课程ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取教师学生"""
    service = TeacherService(db)
    students = service.get_teacher_students(id, semester, course_id)
    return Response(data=students)


@router.get("/{id}/schedule", response_model=Response, summary="获取教师课表")
async def get_teacher_schedule(
    id: int = Path(..., description="教师ID"),
    semester: str = Query(None, description="学期"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取教师课表"""
    service = TeacherService(db)
    schedule = service.get_teacher_schedule(id, semester)
    return Response(data=schedule)
