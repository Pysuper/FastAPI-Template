from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.attendance import Attendance, AttendanceRule
from models.school import Course, Student
from schemas.common import PaginationParams


class AttendanceService:
    """考勤服务类"""

    async def check_in(self, db: AsyncSession, student_id: int, course_id: int, check_time: Optional[datetime] = None):
        """学生签到"""
        # 验证学生和课程是否存在
        student = await db.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生不存在")

        course = await db.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        # 获取考勤规则
        stmt = select(AttendanceRule).where(AttendanceRule.course_id == course_id)
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程未设置考勤规则")

        # 检查是否已签到
        check_date = check_time.date() if check_time else datetime.now().date()
        stmt = select(Attendance).where(
            and_(
                Attendance.student_id == student_id,
                Attendance.course_id == course_id,
                func.date(Attendance.check_in_time) == check_date,
            )
        )
        result = await db.execute(stmt)
        attendance = result.scalar_one_or_none()
        if attendance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="今日已签到")

        # 创建考勤记录
        check_time = check_time or datetime.now()
        attendance = Attendance(student_id=student_id, course_id=course_id, check_in_time=check_time)

        # 判断是否迟到
        rule_start_time = datetime.strptime(rule.start_time, "%H:%M").time()
        if check_time.time() > rule_start_time:
            minutes_late = (
                datetime.combine(check_date, check_time.time()) - datetime.combine(check_date, rule_start_time)
            ).seconds / 60
            if minutes_late > rule.late_threshold:
                attendance.status = "late"

        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
        return attendance

    async def check_out(self, db: AsyncSession, student_id: int, course_id: int, check_time: Optional[datetime] = None):
        """学生签退"""
        # 获取今日考勤记录
        check_date = check_time.date() if check_time else datetime.now().date()
        stmt = select(Attendance).where(
            and_(
                Attendance.student_id == student_id,
                Attendance.course_id == course_id,
                func.date(Attendance.check_in_time) == check_date,
            )
        )
        result = await db.execute(stmt)
        attendance = result.scalar_one_or_none()
        if not attendance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未找到签到记录")

        if attendance.check_out_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已签退")

        # 获取考勤规则
        stmt = select(AttendanceRule).where(AttendanceRule.course_id == course_id)
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程未设置考勤规则")

        # 更新签退时间
        check_time = check_time or datetime.now()
        attendance.check_out_time = check_time

        # 判断是否早退
        rule_end_time = datetime.strptime(rule.end_time, "%H:%M").time()
        if check_time.time() < rule_end_time:
            minutes_early = (
                datetime.combine(check_date, rule_end_time) - datetime.combine(check_date, check_time.time())
            ).seconds / 60
            if minutes_early > rule.early_threshold:
                attendance.status = "early_leave"

        await db.commit()
        await db.refresh(attendance)
        return attendance

    async def get_student_attendance(
        self,
        db: AsyncSession,
        student_id: int,
        course_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        pagination: PaginationParams = PaginationParams(),
    ):
        """获取学生考勤记录"""
        query = select(Attendance).where(Attendance.student_id == student_id)

        if course_id:
            query = query.where(Attendance.course_id == course_id)
        if start_date:
            query = query.where(Attendance.check_in_time >= start_date)
        if end_date:
            query = query.where(Attendance.check_in_time <= end_date)

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        records = result.scalars().all()

        return {"total": total, "items": records, "page": pagination.page, "size": pagination.limit}

    async def get_course_attendance(
        self,
        db: AsyncSession,
        course_id: int,
        date: Optional[datetime] = None,
        pagination: PaginationParams = PaginationParams(),
    ):
        """获取课程考勤记录"""
        query = select(Attendance).where(Attendance.course_id == course_id)

        if date:
            query = query.where(func.date(Attendance.check_in_time) == date.date())

        # 分页
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset(pagination.skip).limit(pagination.limit)

        result = await db.execute(query)
        records = result.scalars().all()

        return {"total": total, "items": records, "page": pagination.page, "size": pagination.limit}

    async def get_attendance_statistics(self, db: AsyncSession, course_id: int, student_id: Optional[int] = None):
        """获取考勤统计信息"""
        query = select(Attendance).where(Attendance.course_id == course_id)

        if student_id:
            query = query.where(Attendance.student_id == student_id)

        result = await db.execute(query)
        records = result.scalars().all()

        total = len(records)
        normal = len([r for r in records if r.status == "normal"])
        late = len([r for r in records if r.status == "late"])
        early_leave = len([r for r in records if r.status == "early_leave"])
        absent = len([r for r in records if r.status == "absent"])

        return {"total": total, "normal": normal, "late": late, "early_leave": early_leave, "absent": absent}

    async def create_attendance_rule(
        self,
        db: AsyncSession,
        course_id: int,
        name: str,
        start_time: str,
        end_time: str,
        late_threshold: int = 15,
        early_threshold: int = 15,
        description: Optional[str] = None,
    ):
        """创建考勤规则"""
        # 验证课程是否存在
        course = await db.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")

        # 验证时间格式
        try:
            datetime.strptime(start_time, "%H:%M")
            datetime.strptime(end_time, "%H:%M")
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="时间格式错误，应为HH:MM")

        # 检查是否已存在规则
        stmt = select(AttendanceRule).where(AttendanceRule.course_id == course_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="课程已存在考勤规则")

        rule = AttendanceRule(
            course_id=course_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            late_threshold=late_threshold,
            early_threshold=early_threshold,
            description=description,
        )

        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule


# 创建服务实例
attendance_service = AttendanceService()
