from datetime import datetime
from typing import Optional, Dict

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache.manager import cache_manager
from models.enrollment import CourseEnrollment, EnrollmentRule, EnrollmentPeriod
from models.school import Course, Student, Semester
from schemas.common import PaginationParams
from schemas.enrollment import (
    CourseEnrollmentCreate,
    CourseEnrollmentUpdate,
    EnrollmentRuleCreate,
    EnrollmentRuleUpdate,
    EnrollmentPeriodCreate,
    EnrollmentPeriodUpdate,
    EnrollmentStatistics,
)


class EnrollmentService:
    """选课服务类"""

    async def create_enrollment(self, db: AsyncSession, enrollment_in: CourseEnrollmentCreate) -> CourseEnrollment:
        """创建选课记录"""
        # 验证学生和课程是否存在
        student = await db.get(Student, enrollment_in.student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生不存在")

        course = await db.get(Course, enrollment_in.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        # 检查是否已选课
        if await self.is_enrolled(db, student_id=enrollment_in.student_id, course_id=enrollment_in.course_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已经选修此课程")

        # 检查选课时段
        if not await self.check_enrollment_period(db, course_id=enrollment_in.course_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不在选课时段内")

        # 检查选课规则
        rule = await self.get_enrollment_rule(db, course_id=enrollment_in.course_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程没有选课规则")

        # 检查课程容量
        if not await self.check_course_capacity(db, course_id=enrollment_in.course_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程已满")

        # 检查选课条件
        if not await self.check_enrollment_requirements(
            db, student_id=enrollment_in.student_id, course_id=enrollment_in.course_id, rule=rule
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不满足选课条件")

        # 创建选课记录
        enrollment = CourseEnrollment(
            student_id=enrollment_in.student_id,
            course_id=enrollment_in.course_id,
            status=enrollment_in.status,
            notes=enrollment_in.notes,
        )

        # 如果不需要审批或自动审批，直接通过
        if not rule.need_approval or rule.auto_approve:
            enrollment.status = "approved"
            enrollment.approval_date = datetime.now()

        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)

        # 更新课程容量缓存
        await self.update_course_capacity_cache(db, course_id=enrollment_in.course_id)

        return enrollment

    async def update_enrollment(
        self, db: AsyncSession, enrollment_id: int, enrollment_in: CourseEnrollmentUpdate
    ) -> CourseEnrollment:
        """更新选课记录"""
        enrollment = await db.get(CourseEnrollment, enrollment_id)
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选课记录不存在")

        # 只能更新待审核状态的记录
        if enrollment.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能更新待审核状态的选课记录")

        # 更新字段
        for field, value in enrollment_in.dict(exclude_unset=True).items():
            setattr(enrollment, field, value)

        # 如果状态变更为已通过，设置审批时间
        if enrollment.status == "approved":
            enrollment.approval_date = datetime.now()

        await db.commit()
        await db.refresh(enrollment)

        # 如果状态变更，更新课程容量缓存
        if enrollment_in.status in ["approved", "rejected", "dropped"]:
            await self.update_course_capacity_cache(db, course_id=enrollment.course_id)

        return enrollment

    async def drop_enrollment(self, db: AsyncSession, enrollment_id: int) -> CourseEnrollment:
        """退课"""
        enrollment = await db.get(CourseEnrollment, enrollment_id)
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选课记录不存在")

        # 检查是否允许退课
        rule = await self.get_enrollment_rule(db, course_id=enrollment.course_id)
        if not rule.allow_drop:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不允许退课")

        # 检查是否在退课期限内
        if rule.drop_deadline and datetime.now() > rule.drop_deadline:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已超过退课期限")

        enrollment.status = "dropped"
        enrollment.drop_date = datetime.now()

        await db.commit()
        await db.refresh(enrollment)

        # 更新课程容量缓存
        await self.update_course_capacity_cache(db, course_id=enrollment.course_id)

        return enrollment

    async def get_enrollment(self, db: AsyncSession, enrollment_id: int) -> CourseEnrollment:
        """获取选课记录"""
        enrollment = await db.get(CourseEnrollment, enrollment_id)
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选课记录不存在")
        return enrollment

    async def get_enrollments(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        student_id: Optional[int] = None,
        course_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict:
        """获取选课记录列表"""
        query = select(CourseEnrollment)

        if student_id:
            query = query.where(CourseEnrollment.student_id == student_id)
        if course_id:
            query = query.where(CourseEnrollment.course_id == course_id)
        if status:
            query = query.where(CourseEnrollment.status == status)

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        enrollments = result.scalars().all()

        return {"total": total, "items": enrollments, "page": pagination.page, "size": pagination.limit}

    async def create_enrollment_rule(self, db: AsyncSession, rule_in: EnrollmentRuleCreate) -> EnrollmentRule:
        """创建选课规则"""
        # 验证课程是否存在
        course = await db.get(Course, rule_in.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        # 检查是否已存在规则
        stmt = select(EnrollmentRule).where(EnrollmentRule.course_id == rule_in.course_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程已存在选课规则")

        rule = EnrollmentRule(**rule_in.dict())
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    async def update_enrollment_rule(
        self, db: AsyncSession, rule_id: int, rule_in: EnrollmentRuleUpdate
    ) -> EnrollmentRule:
        """更新选课规则"""
        rule = await db.get(EnrollmentRule, rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选课规则不存在")

        # 更新字段
        for field, value in rule_in.dict(exclude_unset=True).items():
            setattr(rule, field, value)

        await db.commit()
        await db.refresh(rule)
        return rule

    async def create_enrollment_period(self, db: AsyncSession, period_in: EnrollmentPeriodCreate) -> EnrollmentPeriod:
        """创建选课时段"""
        # 验证学期是否存在
        semester = await db.get(Semester, period_in.semester_id)
        if not semester:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学期不存在")

        period = EnrollmentPeriod(**period_in.dict())
        db.add(period)
        await db.commit()
        await db.refresh(period)
        return period

    async def update_enrollment_period(
        self, db: AsyncSession, period_id: int, period_in: EnrollmentPeriodUpdate
    ) -> EnrollmentPeriod:
        """更新选课时段"""
        period = await db.get(EnrollmentPeriod, period_id)
        if not period:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选课时段不存在")

        # 更新字段
        for field, value in period_in.dict(exclude_unset=True).items():
            setattr(period, field, value)

        await db.commit()
        await db.refresh(period)
        return period

    async def get_enrollment_statistics(
        self, db: AsyncSession, course_id: Optional[int] = None
    ) -> EnrollmentStatistics:
        """获取选课统计信息"""
        # 从缓存获取统计信息
        cache_key = f"enrollment_stats:{course_id or 'all'}"
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            return EnrollmentStatistics(**cached_data)

        # 构建查询
        query = select(CourseEnrollment)
        if course_id:
            query = query.where(CourseEnrollment.course_id == course_id)

        result = await db.execute(query)
        enrollments = result.scalars().all()

        # 获取课程信息
        courses_query = select(Course)
        if course_id:
            courses_query = courses_query.where(Course.id == course_id)

        result = await db.execute(courses_query)
        courses = result.scalars().all()

        # 计算统计信息
        total_courses = len(courses)
        total_students = len(set(e.student_id for e in enrollments if e.status == "approved"))
        avg_students = total_students / total_courses if total_courses > 0 else 0

        # 统计课程容量
        course_stats = {}
        for course in courses:
            course_enrollments = [e for e in enrollments if e.course_id == course.id and e.status == "approved"]
            course_stats[course.id] = len(course_enrollments)

        full_courses = sum(1 for count in course_stats.values() if count >= course.max_students)
        available_courses = total_courses - full_courses

        # 统计待审批数
        pending_approvals = len([e for e in enrollments if e.status == "pending"])

        # 课程分布
        course_distribution = {"0-10": 0, "11-20": 0, "21-30": 0, "31-40": 0, "41+": 0}

        for count in course_stats.values():
            if count <= 10:
                course_distribution["0-10"] += 1
            elif count <= 20:
                course_distribution["11-20"] += 1
            elif count <= 30:
                course_distribution["21-30"] += 1
            elif count <= 40:
                course_distribution["31-40"] += 1
            else:
                course_distribution["41+"] += 1

        stats = EnrollmentStatistics(
            total_courses=total_courses,
            total_students=total_students,
            avg_students_per_course=avg_students,
            full_courses=full_courses,
            available_courses=available_courses,
            pending_approvals=pending_approvals,
            course_distribution=course_distribution,
        )

        # 更新缓存
        await cache_manager.set(cache_key, stats.dict(), expire=300)  # 缓存5分钟

        return stats

    async def is_enrolled(self, db: AsyncSession, student_id: int, course_id: int) -> bool:
        """检查学生是否已选课"""
        result = await db.execute(
            select(CourseEnrollment).where(
                and_(
                    CourseEnrollment.student_id == student_id,
                    CourseEnrollment.course_id == course_id,
                    CourseEnrollment.status != "dropped",
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def check_enrollment_period(self, db: AsyncSession, course_id: int) -> bool:
        """检查是否在选课时段内"""
        # 获取当前学期
        now = datetime.now()
        stmt = select(Semester).where(and_(Semester.start_date <= now, Semester.end_date >= now))
        result = await db.execute(stmt)
        semester = result.scalar_one_or_none()
        if not semester:
            return False

        # 检查选课时段
        stmt = select(EnrollmentPeriod).where(
            and_(
                EnrollmentPeriod.semester_id == semester.id,
                EnrollmentPeriod.start_date <= now,
                EnrollmentPeriod.end_date >= now,
                EnrollmentPeriod.is_active == True,
                EnrollmentPeriod.status == "ongoing",
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def check_course_capacity(self, db: AsyncSession, course_id: int) -> bool:
        """检查课程容量"""
        # 从缓存获取课程容量信息
        cache_key = f"course_capacity:{course_id}"
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            return cached_data["current_count"] < cached_data["max_students"]

        # 从数据库获取信息
        course = await db.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        result = await db.execute(
            select(func.count()).where(
                and_(CourseEnrollment.course_id == course_id, CourseEnrollment.status == "approved")
            )
        )
        current_count = result.scalar_one()

        # 更新缓存
        await cache_manager.set(
            cache_key, {"current_count": current_count, "max_students": course.max_students}, expire=300  # 缓存5分钟
        )

        return current_count < course.max_students

    async def check_enrollment_requirements(
        self, db: AsyncSession, student_id: int, course_id: int, rule: EnrollmentRule
    ) -> bool:
        """检查选课条件"""
        student = await db.get(Student, student_id)
        if not student:
            return False

        # 检查年级要求
        if rule.year_requirements and str(student.year) not in rule.year_requirements.split(","):
            return False

        # 检查专业要求
        if rule.major_requirements and str(student.major_id) not in rule.major_requirements.split(","):
            return False

        # 检查先修课程要求
        if rule.prerequisites:
            prerequisite_courses = rule.prerequisites.split(",")
            for course_id in prerequisite_courses:
                result = await db.execute(
                    select(CourseEnrollment).where(
                        and_(
                            CourseEnrollment.student_id == student_id,
                            CourseEnrollment.course_id == int(course_id),
                            CourseEnrollment.status == "completed",
                        )
                    )
                )
                if not result.scalar_one_or_none():
                    return False

        # 检查成绩要求
        if rule.grade_requirements:
            # 这里可以添加更复杂的成绩要求检查逻辑
            pass

        return True

    async def update_course_capacity_cache(self, db: AsyncSession, course_id: int):
        """更新课程容量缓存"""
        cache_key = f"course_capacity:{course_id}"
        await cache_manager.delete(cache_key)


# 创建服务实例
enrollment_service = EnrollmentService()
