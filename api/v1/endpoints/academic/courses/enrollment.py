from typing import List

from fastapi import APIRouter, Depends, Query, Path, Body, UploadFile, File, HTTPException
from oss2.exceptions import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.schemas.common import Response
from dependencies.auth import get_current_active_user, get_current_user
from dependencies.db import get_db
from exceptions.system.database import NotFoundException
from middlewares import PageResponse
from models.rbac import User
from schemas.school import (
    CourseEnrollmentCreate,
    CourseEnrollmentUpdate,
    CourseEnrollmentResponse,
    CourseEnrollmentStatusUpdate,
    CourseEnrollmentScoreUpdate,
    CourseEnrollmentGradeUpdate,
    CourseEnrollmentInDB,
)
from services.enrollment import enrollment_service

router = APIRouter(prefix="/courses/{course_id}/enrollments", tags=["课程选课"])


@router.get("/", response_model=PageResponse[CourseEnrollmentResponse], summary="获取选课列表")
async def get_enrollments(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    status: str = Query(None, description="状态"),
    student_id: int = Query(None, description="学��ID"),
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
    """获取选课列表"""
    service = CourseEnrollmentService(db)
    total, items = service.get_enrollments(
        course_id=course_id,
        semester=semester,
        status=status,
        student_id=student_id,
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


def CourseEnrollmentService(db):
    pass


@router.post("/", response_model=Response, summary="创建选课")
async def create_enrollment(
    course_id: int = Path(..., description="课程ID"),
    data: CourseEnrollmentCreate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建选课"""
    service = CourseEnrollmentService(db)
    enrollment = service.create_enrollment(course_id, data)
    return Response(data={"id": enrollment.id})


@router.get("/{id}", response_model=Response, summary="获取选课详情")
async def get_enrollment(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="选课ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取选课详情"""
    service = CourseEnrollmentService(db)
    enrollment = service.get_enrollment(course_id, id)
    if not enrollment:
        raise NotFoundException("选课不存在")
    return Response(data=enrollment)


@router.put("/{id}", response_model=Response, summary="更新选课")
async def update_enrollment(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="选课ID"),
    data: CourseEnrollmentUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新选课"""
    service = CourseEnrollmentService(db)
    enrollment = service.update_enrollment(course_id, id, data)
    return Response()


@router.delete("/{id}", response_model=Response, summary="删除选课")
async def delete_enrollment(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="选课ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除选课"""
    service = CourseEnrollmentService(db)
    service.delete_enrollment(course_id, id)
    return Response()


@router.put("/{id}/status", response_model=Response, summary="更新选课状态")
async def update_enrollment_status(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="选课ID"),
    data: CourseEnrollmentStatusUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新选课状态"""
    service = CourseEnrollmentService(db)
    service.update_enrollment_status(course_id, id, data.status)
    return Response()


@router.put("/{id}/score", response_model=Response, summary="更新选课成绩")
async def update_enrollment_score(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="选课ID"),
    data: CourseEnrollmentScoreUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新选课成绩"""
    service = CourseEnrollmentService(db)
    service.update_enrollment_score(course_id, id, data.score)
    return Response()


@router.put("/{id}/grade", response_model=Response, summary="更新选课等级")
async def update_enrollment_grade(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="选课ID"),
    data: CourseEnrollmentGradeUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新选课等级"""
    service = CourseEnrollmentService(db)
    service.update_enrollment_grade(course_id, id, data.grade)
    return Response()


@router.post("/batch", response_model=Response, summary="批量选课")
async def batch_enroll(
    course_id: int = Path(..., description="课程ID"),
    data: List[CourseEnrollmentCreate] = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """批量选课"""
    service = CourseEnrollmentService(db)
    result = service.batch_enroll(course_id, data)
    return Response(data=result)


@router.post("/import", response_model=Response, summary="导入选课")
async def import_enrollments(
    course_id: int = Path(..., description="课程ID"),
    file: UploadFile = File(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导入选课"""
    service = CourseEnrollmentService(db)
    result = service.import_enrollments(course_id, file)
    return Response(data=result)


@router.get("/export", response_model=Response, summary="导出选课")
async def export_enrollments(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    status: str = Query(None, description="状态"),
    student_id: int = Query(None, description="学生ID"),
    class_id: int = Query(None, description="班级ID"),
    major_id: int = Query(None, description="专业ID"),
    department_id: int = Query(None, description="院系ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导出选课"""
    service = CourseEnrollmentService(db)
    result = service.export_enrollments(
        course_id=course_id,
        semester=semester,
        status=status,
        student_id=student_id,
        class_id=class_id,
        major_id=major_id,
        department_id=department_id,
    )
    return Response(data=result)


@router.get("/stats", response_model=Response, summary="获取选课统计")
async def get_enrollment_stats(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取选课统计"""
    service = CourseEnrollmentService(db)
    stats = service.get_enrollment_stats(
        course_id=course_id, semester=semester, start_time=start_time, end_time=end_time
    )
    return Response(data=stats)


@router.post("/enrollments/batch", response_model=List[CourseEnrollmentInDB])
async def batch_create_enrollments(
    *,
    db: AsyncSession = Depends(async_db),
    student_ids: List[int] = Query(..., description="学生ID列表"),
    course_id: int = Query(..., description="课程ID"),
    current_user: User = Depends(get_current_user),
) -> List[CourseEnrollmentInDB]:
    """批量创建选课记录"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await enrollment_service.batch_create_enrollments(db, student_ids=student_ids, course_id=course_id)
