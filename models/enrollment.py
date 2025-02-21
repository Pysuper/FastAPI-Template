from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, JSON, Text, String, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class EnrollmentStatus(str, PyEnum):
    """选课状态"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    DROPPED = "dropped"  # 已退课
    COMPLETED = "completed"  # 已完成


class EnrollmentPeriodType(str, PyEnum):
    """选课时段类型"""

    NORMAL = "normal"  # 正常选课
    SUPPLEMENTARY = "supplementary"  # 补选
    WITHDRAWAL = "withdrawal"  # 退课
    ADJUSTMENT = "adjustment"  # 调课


class EnrollmentPeriodStatus(str, PyEnum):
    """选课时段状态"""

    UPCOMING = "upcoming"  # 即将开始
    ONGOING = "ongoing"  # 进行中
    ENDED = "ended"  # 已结束
    CANCELLED = "cancelled"  # 已取消


class CourseEnrollment(AbstractModel):
    """选课记录模型"""

    __tablename__ = "course_enrollments"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="选课名称")
    status: Mapped[EnrollmentStatus] = mapped_column(
        default=EnrollmentStatus.PENDING,
        nullable=False,
        index=True,
        comment="选课状态",
    )

    # 选课时间
    enrollment_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, comment="选课时间")
    approval_date: Mapped[Optional[datetime]] = mapped_column(comment="审批时间")
    drop_date: Mapped[Optional[datetime]] = mapped_column(comment="退课时间")

    # 选课成绩
    score: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="成绩")
    grade_point: Mapped[Optional[float]] = mapped_column(Float(precision=1), comment="绩点")
    attendance_rate: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="出勤率")

    # 选课备注
    notes: Mapped[Optional[str]] = mapped_column(Text, comment="备注")
    drop_reason: Mapped[Optional[str]] = mapped_column(Text, comment="退课原因")

    # 外键关联
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生ID",
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="课程ID",
    )
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("semesters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="学期ID",
    )
    period_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("enrollment_periods.id", ondelete="SET NULL"),
        comment="选课时段ID",
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"), comment="审批人ID"
    )

    # 关联关系
    student: Mapped["Student"] = relationship("Student", back_populates="enrollments", lazy="joined")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments", lazy="joined")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="enrollments", lazy="joined")
    period: Mapped[Optional["EnrollmentPeriod"]] = relationship(
        "EnrollmentPeriod",
        back_populates="enrollments",
        lazy="joined",
    )
    approver: Mapped[Optional["Teacher"]] = relationship("Teacher", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_course_enrollments_unique",
            "student_id",
            "course_id",
            "semester_id",
            unique=True,
        ),
        Index(
            "ix_course_enrollments_status_period",
            "status",
            "period_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<CourseEnrollment {self.student.name} {self.course.name}>"


class EnrollmentRule(AbstractModel):
    """选课规则模型"""

    __tablename__ = "enrollment_rules"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="规则名称")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="规则描述")

    # 选课时间限制
    start_date: Mapped[datetime] = mapped_column(nullable=False, comment="开始时间")
    end_date: Mapped[datetime] = mapped_column(nullable=False, comment="结束时间")

    # 选课人数限制
    min_students: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="最少选课人数")
    max_students: Mapped[int] = mapped_column(Integer, nullable=False, comment="最大选课人数")

    # 选课条件
    prerequisites: Mapped[Optional[str]] = mapped_column(Text, comment="先修课程要求")
    grade_requirements: Mapped[Optional[str]] = mapped_column(Text, comment="成绩要求")
    year_requirements: Mapped[Optional[str]] = mapped_column(Text, comment="年级要求")
    major_requirements: Mapped[Optional[str]] = mapped_column(Text, comment="专业要求")

    # 审批设置
    need_approval: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否需要审批")
    auto_approve: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否自动审批")
    approval_conditions: Mapped[Optional[str]] = mapped_column(Text, comment="自动审批条件")

    # 退课设置
    allow_drop: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否允许退课")
    drop_deadline: Mapped[Optional[datetime]] = mapped_column(comment="退课截止时间")
    drop_conditions: Mapped[Optional[str]] = mapped_column(Text, comment="退课条件")

    # 外键关联
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID"
    )

    # 关联关系
    course: Mapped["Course"] = relationship("Course", back_populates="enrollment_rules", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_enrollment_rules_course_date",
            "course_id",
            "start_date",
            "end_date",
        ),
    )

    def __repr__(self) -> str:
        return f"<EnrollmentRule {self.name}>"


class EnrollmentPeriod(AbstractModel):
    """选课时段模型"""

    __tablename__ = "enrollment_periods"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="时段名称")
    type: Mapped[EnrollmentPeriodType] = mapped_column(
        default=EnrollmentPeriodType.NORMAL,
        nullable=False,
        index=True,
        comment="时段类型",
    )
    status: Mapped[EnrollmentPeriodStatus] = mapped_column(
        default=EnrollmentPeriodStatus.UPCOMING,
        nullable=False,
        index=True,
        comment="时段状态",
    )

    # 时段时间
    start_date: Mapped[datetime] = mapped_column(nullable=False, comment="开始时间")
    end_date: Mapped[datetime] = mapped_column(nullable=False, comment="结束时间")

    # 选课对象
    target_grades: Mapped[Optional[str]] = mapped_column(Text, comment="目标年级")
    target_majors: Mapped[Optional[str]] = mapped_column(Text, comment="目标专业")
    target_students: Mapped[Optional[str]] = mapped_column(Text, comment="目标学生")

    # 选课限制
    max_courses: Mapped[Optional[int]] = mapped_column(Integer, comment="最大选课数")
    min_credits: Mapped[Optional[int]] = mapped_column(Integer, comment="最少学分")
    max_credits: Mapped[Optional[int]] = mapped_column(Integer, comment="最大学分")

    # 外键关联
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("semesters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学期ID",
    )

    # 关联关系
    semester: Mapped["Semester"] = relationship("Semester", back_populates="enrollment_periods", lazy="joined")
    enrollments: Mapped[List["CourseEnrollment"]] = relationship(
        "CourseEnrollment",
        back_populates="period",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_enrollment_periods_semester_date",
            "semester_id",
            "start_date",
            "end_date",
        ),
        Index(
            "ix_enrollment_periods_type_status",
            "type",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return f"<EnrollmentPeriod {self.name} {self.type}>"
