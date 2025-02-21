from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from core.db import get_db
from core.exceptions import NotFoundException, ValidationException
from core.security import get_current_user, get_current_active_user
from models.student import Student
from schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentFilter,
    StudentResponse,
    StudentStatusUpdate,
    StudentTransferUpdate,
    StudentGraduateUpdate,
)
from schemas.common import Response, PageResponse
from services.student import StudentService

router = APIRouter(prefix="/students", tags=["学生"])


@router.get("/", response_model=PageResponse[StudentResponse], summary="获取学生列表")
async def get_students(
    query: str = Query(None, description="搜索关键词"),
    status: str = Query(None, description="状态"),
    grade: str = Query(None, description="年级"),
    class_id: int = Query(None, description="班级ID"),
    major_id: int = Query(None, description="专业ID"),
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
    """获取学生列表"""
    service = StudentService(db)
    total, items = service.get_students(
        query=query,
        status=status,
        grade=grade,
        class_id=class_id,
        major_id=major_id,
        department_id=department_id,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
        sort=sort,
        order=order,
    )
    return PageResponse(total=total, items=items, page=page, size=size)


@router.post("/", response_model=Response, summary="创建学生")
async def create_student(
    data: StudentCreate, db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)
):
    """创建学生"""
    service = StudentService(db)
    student = service.create_student(data)
    return Response(data={"id": student.id})


@router.get("/{id}", response_model=Response, summary="获取学生详情")
async def get_student(
    id: int = Path(..., description="学生ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取学生详情"""
    service = StudentService(db)
    student = service.get_student(id)
    if not student:
        raise NotFoundException("学生不存在")
    return Response(data=student)


@router.put("/{id}", response_model=Response, summary="更新学生")
async def update_student(
    id: int = Path(..., description="学生ID"),
    data: StudentUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新学生"""
    service = StudentService(db)
    student = service.update_student(id, data)
    return Response()


@router.delete("/{id}", response_model=Response, summary="删除学生")
async def delete_student(
    id: int = Path(..., description="学生ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除学生"""
    service = StudentService(db)
    service.delete_student(id)
    return Response()


@router.put("/{id}/status", response_model=Response, summary="更新学生状态")
async def update_student_status(
    id: int = Path(..., description="学生ID"),
    data: StudentStatusUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新学生状态"""
    service = StudentService(db)
    service.update_student_status(id, data.status)
    return Response()


@router.post("/{id}/transfer", response_model=Response, summary="学生转班")
async def transfer_student(
    id: int = Path(..., description="学生ID"),
    data: StudentTransferUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """学生转班"""
    service = StudentService(db)
    service.transfer_student(id, data.class_id)
    return Response()


@router.post("/{id}/graduate", response_model=Response, summary="学生毕业")
async def graduate_student(
    id: int = Path(..., description="学生ID"),
    data: StudentGraduateUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """学生毕业"""
    service = StudentService(db)
    service.graduate_student(id, data.graduation_date)
    return Response()


@router.get("/classes", response_model=Response, summary="获取班级列表")
async def get_classes(
    grade: str = Query(None, description="年级"),
    major_id: int = Query(None, description="专业ID"),
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取班级列表"""
    service = StudentService(db)
    classes = service.get_classes(grade=grade, major_id=major_id, department_id=department_id)
    return Response(data=classes)


@router.get("/grades", response_model=Response, summary="获取年级列表")
async def get_grades(db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)):
    """获取年级列表"""
    service = StudentService(db)
    grades = service.get_grades()
    return Response(data=grades)


@router.get("/majors", response_model=Response, summary="获取专业列表")
async def get_majors(
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取专业列表"""
    service = StudentService(db)
    majors = service.get_majors(department_id)
    return Response(data=majors)


@router.get("/departments", response_model=Response, summary="获取院系列表")
async def get_departments(db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)):
    """获取院系列表"""
    service = StudentService(db)
    departments = service.get_departments()
    return Response(data=departments)


@router.post("/import", response_model=Response, summary="导入学生")
async def import_students(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)
):
    """导入学生"""
    service = StudentService(db)
    result = service.import_students(file)
    return Response(data=result)


@router.get("/export", response_model=Response, summary="导出学生")
async def export_students(
    query: str = Query(None, description="搜索关键词"),
    status: str = Query(None, description="状态"),
    grade: str = Query(None, description="年级"),
    class_id: int = Query(None, description="班级ID"),
    major_id: int = Query(None, description="专业ID"),
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导出学生"""
    service = StudentService(db)
    result = service.export_students(
        query=query, status=status, grade=grade, class_id=class_id, major_id=major_id, department_id=department_id
    )
    return Response(data=result)


@router.get("/stats", response_model=Response, summary="获取学生统计")
async def get_student_stats(
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取学生统计"""
    service = StudentService(db)
    stats = service.get_student_stats(start_time=start_time, end_time=end_time)
    return Response(data=stats)
