from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.deps import get_db
from security.core.security import get_current_user
from models.rbac import User
from schemas.common import PaginationParams
from services.attendance import attendance_service

router = APIRouter()


@router.post("/check-in")
async def check_in(
    *,
    db: AsyncSession = Depends(async_db),
    student_id: int = Query(..., description="学生ID"),
    course_id: int = Query(..., description="课程ID"),
    check_time: Optional[datetime] = Query(None, description="签到时间"),
    current_user: User = Depends(get_current_user),
):
    """学生签到"""
    # 验证权限
    if not current_user.is_superuser and current_user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await attendance_service.check_in(db, student_id=student_id, course_id=course_id, check_time=check_time)


@router.post("/check-out")
async def check_out(
    *,
    db: AsyncSession = Depends(async_db),
    student_id: int = Query(..., description="学生ID"),
    course_id: int = Query(..., description="课程ID"),
    check_time: Optional[datetime] = Query(None, description="签退时间"),
    current_user: User = Depends(get_current_user),
):
    """学生签退"""
    # 验证权限
    if not current_user.is_superuser and current_user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await attendance_service.check_out(db, student_id=student_id, course_id=course_id, check_time=check_time)


@router.get("/student/{student_id}")
async def get_student_attendance(
    *,
    db: AsyncSession = Depends(async_db),
    student_id: int,
    course_id: Optional[int] = Query(None, description="课程ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    """获取学生考勤记录"""
    # 验证权限
    if not current_user.is_superuser and current_user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await attendance_service.get_student_attendance(
        db, student_id=student_id, course_id=course_id, start_date=start_date, end_date=end_date, pagination=pagination
    )


@router.get("/course/{course_id}")
async def get_course_attendance(
    *,
    db: AsyncSession = Depends(async_db),
    course_id: int,
    date: Optional[datetime] = Query(None, description="日期"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    """获取课程考勤记录"""
    return await attendance_service.get_course_attendance(db, course_id=course_id, date=date, pagination=pagination)


@router.get("/statistics")
async def get_attendance_statistics(
    *,
    db: AsyncSession = Depends(async_db),
    course_id: int = Query(..., description="课程ID"),
    student_id: Optional[int] = Query(None, description="学生ID"),
    current_user: User = Depends(get_current_user),
):
    """获取考勤统计信息"""
    return await attendance_service.get_attendance_statistics(db, course_id=course_id, student_id=student_id)


@router.post("/rules")
async def create_attendance_rule(
    *,
    db: AsyncSession = Depends(async_db),
    course_id: int = Query(..., description="课程ID"),
    name: str = Query(..., description="规则名称"),
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    late_threshold: int = Query(15, description="迟到阈值（分钟）"),
    early_threshold: int = Query(15, description="早退阈值（分钟）"),
    description: Optional[str] = Query(None, description="规则描述"),
    current_user: User = Depends(get_current_user),
):
    """创建考勤规则"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await attendance_service.create_attendance_rule(
        db,
        course_id=course_id,
        name=name,
        start_time=start_time,
        end_time=end_time,
        late_threshold=late_threshold,
        early_threshold=early_threshold,
        description=description,
    )
