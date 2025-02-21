from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.school import Course, Teacher
from models.teaching import TeachingPlan, TeachingPlanDetail, TeachingSchedule
from schemas.common import PaginationParams
from schemas.teaching import (
    TeachingPlanCreate,
    TeachingPlanUpdate,
    TeachingScheduleCreate,
    TeachingScheduleUpdate,
)


class TeachingService:
    """教学计划服务类"""

    async def create_plan(self, db: AsyncSession, plan_in: TeachingPlanCreate) -> TeachingPlan:
        """创建教学计划"""
        # 验证课程和教师是否存在
        course = await db.get(Course, plan_in.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        teacher = await db.get(Teacher, plan_in.teacher_id)
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教师不存在")

        # 检查是否已存在同一学期的教学计划
        stmt = select(TeachingPlan).where(
            and_(
                TeachingPlan.course_id == plan_in.course_id,
                TeachingPlan.semester == plan_in.semester,
                TeachingPlan.year == plan_in.year,
            )
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该学期已存在教学计划")

        # 创建教学计划
        plan = TeachingPlan(
            name=plan_in.name,
            description=plan_in.description,
            semester=plan_in.semester,
            year=plan_in.year,
            status=plan_in.status,
            course_id=plan_in.course_id,
            teacher_id=plan_in.teacher_id,
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)

        # 创建教学计划详情
        for detail_in in plan_in.details:
            detail = TeachingPlanDetail(
                plan_id=plan.id,
                week=detail_in.week,
                hours=detail_in.hours,
                content=detail_in.content,
                objectives=detail_in.objectives,
                methods=detail_in.methods,
                resources=detail_in.resources,
                assignments=detail_in.assignments,
            )
            db.add(detail)

        await db.commit()
        await db.refresh(plan)
        return plan

    async def update_plan(self, db: AsyncSession, plan_id: int, plan_in: TeachingPlanUpdate) -> TeachingPlan:
        """更新教学计划"""
        # 获取教学计划
        plan = await db.get(TeachingPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学计划不存在")

        # 只有草稿状态的计划可以更新
        if plan.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能更新草稿状态的教学计划")

        # 更新基本信息
        for field, value in plan_in.dict(exclude_unset=True).items():
            if field != "details":
                setattr(plan, field, value)

        # 更新教学计划详情
        if plan_in.details:
            # 删除原有详情
            stmt = select(TeachingPlanDetail).where(TeachingPlanDetail.plan_id == plan_id)
            result = await db.execute(stmt)
            for detail in result.scalars().all():
                await db.delete(detail)

            # 创建新的详情
            for detail_in in plan_in.details:
                detail = TeachingPlanDetail(
                    plan_id=plan.id,
                    week=detail_in.week,
                    hours=detail_in.hours,
                    content=detail_in.content,
                    objectives=detail_in.objectives,
                    methods=detail_in.methods,
                    resources=detail_in.resources,
                    assignments=detail_in.assignments,
                )
                db.add(detail)

        await db.commit()
        await db.refresh(plan)
        return plan

    async def get_plan(self, db: AsyncSession, plan_id: int) -> TeachingPlan:
        """获取教学计划"""
        plan = await db.get(TeachingPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学计划不存在")
        return plan

    async def get_plans(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        semester: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[TeachingPlan]:
        """获取教学计划列表"""
        query = select(TeachingPlan)

        if course_id:
            query = query.where(TeachingPlan.course_id == course_id)
        if teacher_id:
            query = query.where(TeachingPlan.teacher_id == teacher_id)
        if semester:
            query = query.where(TeachingPlan.semester == semester)
        if year:
            query = query.where(TeachingPlan.year == year)
        if status:
            query = query.where(TeachingPlan.status == status)

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        plans = result.scalars().all()

        return {"total": total, "items": plans, "page": pagination.page, "size": pagination.limit}

    async def delete_plan(self, db: AsyncSession, plan_id: int) -> bool:
        """删除教学计划"""
        plan = await db.get(TeachingPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学计划不存在")

        # 只能删除草稿状态的计划
        if plan.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能删除草稿状态的教学计划")

        await db.delete(plan)
        await db.commit()
        return True

    async def publish_plan(self, db: AsyncSession, plan_id: int) -> TeachingPlan:
        """发布教学计划"""
        plan = await db.get(TeachingPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学计划不存在")

        # 只能发布草稿状态的计划
        if plan.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能发布草��状态的教学计划")

        # 检查是否有教学计划详情
        stmt = select(TeachingPlanDetail).where(TeachingPlanDetail.plan_id == plan_id)
        result = await db.execute(stmt)
        if not result.scalars().all():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="教学计划没有详细内容")

        plan.status = "published"
        await db.commit()
        await db.refresh(plan)
        return plan

    async def archive_plan(self, db: AsyncSession, plan_id: int) -> TeachingPlan:
        """归档教学计划"""
        plan = await db.get(TeachingPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学计划不存在")

        # 只能归档已发布状态的计划
        if plan.status != "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能归档已发布状态的教学计划")

        plan.status = "archived"
        await db.commit()
        await db.refresh(plan)
        return plan

    async def create_schedule(self, db: AsyncSession, schedule_in: TeachingScheduleCreate) -> TeachingSchedule:
        """创建教学进度"""
        # 验证教学计划和详情是否存在
        plan = await db.get(TeachingPlan, schedule_in.plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学计划不存在")

        detail = await db.get(TeachingPlanDetail, schedule_in.detail_id)
        if not detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学计划详情不存在")

        # 创建教学进度
        schedule = TeachingSchedule(
            plan_id=schedule_in.plan_id,
            detail_id=schedule_in.detail_id,
            actual_date=schedule_in.actual_date,
            actual_content=schedule_in.actual_content,
            completion_rate=schedule_in.completion_rate,
            status=schedule_in.status,
            notes=schedule_in.notes,
        )

        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)
        return schedule

    async def update_schedule(
        self, db: AsyncSession, schedule_id: int, schedule_in: TeachingScheduleUpdate
    ) -> TeachingSchedule:
        """更新教学进度"""
        schedule = await db.get(TeachingSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学进度不存在")

        # 更新字段
        for field, value in schedule_in.dict(exclude_unset=True).items():
            setattr(schedule, field, value)

        await db.commit()
        await db.refresh(schedule)
        return schedule

    async def get_schedule(self, db: AsyncSession, schedule_id: int) -> TeachingSchedule:
        """获取教学进度"""
        schedule = await db.get(TeachingSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学进度不存在")
        return schedule

    async def get_schedules(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        plan_id: Optional[int] = None,
        detail_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TeachingSchedule]:
        """获取教学进度列表"""
        query = select(TeachingSchedule)

        if plan_id:
            query = query.where(TeachingSchedule.plan_id == plan_id)
        if detail_id:
            query = query.where(TeachingSchedule.detail_id == detail_id)
        if status:
            query = query.where(TeachingSchedule.status == status)
        if start_date:
            query = query.where(TeachingSchedule.actual_date >= start_date)
        if end_date:
            query = query.where(TeachingSchedule.actual_date <= end_date)

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        schedules = result.scalars().all()

        return {"total": total, "items": schedules, "page": pagination.page, "size": pagination.limit}


# 创建服务实例
teaching_service = TeachingService()
