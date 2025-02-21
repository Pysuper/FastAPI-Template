from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.metrics.pagination import PaginationParams
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.services.teaching import teaching_service
from models.user import User
from schemas.teaching import (
    TeachingPlanCreate,
    TeachingPlanInDB,
    TeachingPlanUpdate,
    TeachingScheduleCreate,
    TeachingScheduleInDB,
    TeachingScheduleUpdate,
)

router = APIRouter()


@router.post("/plans", response_model=TeachingPlanInDB)
async def create_teaching_plan(
    *,
    db: AsyncSession = Depends(async_db),
    plan_in: TeachingPlanCreate,
    current_user: User = Depends(get_current_user),
):
    """创建教学计划"""
    # 验证权限
    if not current_user.is_superuser and current_user.id != plan_in.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await teaching_service.create_plan(db, plan_in=plan_in)


@router.put("/plans/{plan_id}", response_model=TeachingPlanInDB)
async def update_teaching_plan(
    *,
    db: AsyncSession = Depends(async_db),
    plan_id: int,
    plan_in: TeachingPlanUpdate,
    current_user: User = Depends(get_current_user),
):
    """更新教学计划"""
    # 获取教学计划
    plan = await teaching_service.get_plan(db, plan_id=plan_id)

    # 验证权限
    if not current_user.is_superuser and current_user.id != plan.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await teaching_service.update_plan(db, plan_id=plan_id, plan_in=plan_in)


@router.get("/plans/{plan_id}", response_model=TeachingPlanInDB)
async def get_teaching_plan(
    *,
    db: AsyncSession = Depends(async_db),
    plan_id: int,
    current_user: User = Depends(get_current_user),
):
    """获取教学计划"""
    return await teaching_service.get_plan(db, plan_id=plan_id)


@router.get("/plans", response_model=dict)
async def get_teaching_plans(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    course_id: Optional[int] = Query(None, description="课程ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    semester: Optional[str] = Query(None, description="学期"),
    year: Optional[int] = Query(None, description="学年"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(get_current_user),
):
    """获取教学计划列表"""
    return await teaching_service.get_plans(
        db,
        pagination=pagination,
        course_id=course_id,
        teacher_id=teacher_id,
        semester=semester,
        year=year,
        status=status,
    )


@router.delete("/plans/{plan_id}")
async def delete_teaching_plan(
    *,
    db: AsyncSession = Depends(async_db),
    plan_id: int,
    current_user: User = Depends(get_current_user),
):
    """删除教学计划"""
    # 获取教学计划
    plan = await teaching_service.get_plan(db, plan_id=plan_id)

    # 验证权限
    if not current_user.is_superuser and current_user.id != plan.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限执行此操作",
        )

    return await teaching_service.delete_plan(db, plan_id=plan_id)


@router.post("/plans/{plan_id}/publish", response_model=TeachingPlanInDB)
async def publish_teaching_plan(
    *,
    db: AsyncSession = Depends(async_db),
    plan_id: int,
    current_user: User = Depends(get_current_user),
):
    """发布教学计划"""
    # 获取教学计划
    plan = await teaching_service.get_plan(db, plan_id=plan_id)

    # 验证权限
    if not current_user.is_superuser and current_user.id != plan.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await teaching_service.publish_plan(db, plan_id=plan_id)


@router.post("/plans/{plan_id}/archive", response_model=TeachingPlanInDB)
async def archive_teaching_plan(
    *,
    db: AsyncSession = Depends(async_db),
    plan_id: int,
    current_user: User = Depends(get_current_user),
):
    """归档教学计划"""
    # 获取教学计划
    plan = await teaching_service.get_plan(db, plan_id=plan_id)

    # 验证权限
    if not current_user.is_superuser and current_user.id != plan.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await teaching_service.archive_plan(db, plan_id=plan_id)


@router.post("/schedules", response_model=TeachingScheduleInDB)
async def create_teaching_schedule(
    *,
    db: AsyncSession = Depends(async_db),
    schedule_in: TeachingScheduleCreate,
    current_user: User = Depends(get_current_user),
):
    """创建教学进度"""
    # 获取教学计划
    plan = await teaching_service.get_plan(db, plan_id=schedule_in.plan_id)

    # 验证权限
    if not current_user.is_superuser and current_user.id != plan.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await teaching_service.create_schedule(db, schedule_in=schedule_in)


@router.put("/schedules/{schedule_id}", response_model=TeachingScheduleInDB)
async def update_teaching_schedule(
    *,
    db: AsyncSession = Depends(async_db),
    schedule_id: int,
    schedule_in: TeachingScheduleUpdate,
    current_user: User = Depends(get_current_user),
):
    """更新教学进度"""
    # 获取教学进度
    schedule = await teaching_service.get_schedule(db, schedule_id=schedule_id)

    # 获取教学计划
    plan = await teaching_service.get_plan(db, plan_id=schedule.plan_id)

    # 验证权限
    if not current_user.is_superuser and current_user.id != plan.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")

    return await teaching_service.update_schedule(
        db,
        schedule_id=schedule_id,
        schedule_in=schedule_in,
    )


@router.get("/schedules/{schedule_id}", response_model=TeachingScheduleInDB)
async def get_teaching_schedule(
    *,
    db: AsyncSession = Depends(async_db),
    schedule_id: int,
    current_user: User = Depends(get_current_user),
):
    """获取教学进度"""
    return await teaching_service.get_schedule(db, schedule_id=schedule_id)


@router.get("/schedules", response_model=dict)
async def get_teaching_schedules(
    *,
    db: AsyncSession = Depends(async_db),
    pagination: PaginationParams = Depends(),
    plan_id: Optional[int] = Query(None, description="教学计划ID"),
    detail_id: Optional[int] = Query(None, description="教学计划详情ID"),
    status: Optional[str] = Query(None, description="状态"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
):
    """获取教学进度列表"""
    return await teaching_service.get_schedules(
        db,
        pagination=pagination,
        plan_id=plan_id,
        detail_id=detail_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
