# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：teacher.py
@Author  ：PySuper
@Date    ：2024/12/30 17:09 
@Desc    ：Speedy teacher.py
"""

from datetime import datetime, date
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import String, ForeignKey, Date, Text, Float, Boolean, DateTime, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class TeacherStatus(str, PyEnum):
    """教师状态"""

    ACTIVE = "active"  # 在职
    RETIRED = "retired"  # 退休
    RESIGNED = "resigned"  # 离职
    SUSPENDED = "suspended"  # 停职
    ON_LEAVE = "on_leave"  # 请假


class TeacherTitle(str, PyEnum):
    """教师职称"""

    PROFESSOR = "professor"  # 教授
    ASSOCIATE = "associate"  # 副教授
    LECTURER = "lecturer"  # 讲师
    ASSISTANT = "assistant"  # 助教
    OTHER = "other"  # 其他


class TeachingPlanStatus(str, PyEnum):
    """教学计划状态"""

    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审核
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 已归档
    CANCELLED = "cancelled"  # 已取消


class TeachingScheduleStatus(str, PyEnum):
    """教学进度状态"""

    PENDING = "pending"  # 待完成
    COMPLETED = "completed"  # 已完成
    DELAYED = "delayed"  # 延期
    CANCELLED = "cancelled"  # 取消


class TeacherRole(str, PyEnum):
    """教师角色"""

    LECTURER = "lecturer"  # 主讲
    ASSISTANT = "assistant"  # 助教
    SUBSTITUTE = "substitute"  # 代课
    GUEST = "guest"  # 客座


class TeacherAttendanceType(str, PyEnum):
    """教师考勤类型"""

    NORMAL = "normal"  # 正常
    LATE = "late"  # 迟到
    EARLY = "early"  # 早退
    ABSENT = "absent"  # 缺勤
    LEAVE = "leave"  # 请假


class TeacherLeaveType(str, PyEnum):
    """教师请假类型"""

    SICK = "sick"  # 病假
    PERSONAL = "personal"  # 事假
    ANNUAL = "annual"  # 年假
    OFFICIAL = "official"  # 公假
    OTHER = "other"  # 其他


class TeacherAttendanceStatus(str, PyEnum):
    """教师考勤审批状态"""

    PENDING = "pending"  # 待审批
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已驳回
    CANCELLED = "cancelled"  # 已取消


class Teacher(AbstractModel):
    """教师基本信息模型"""

    __tablename__ = "teachers"

    # 继承基类的code字段作为工号
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="姓名")
    title: Mapped[TeacherTitle] = mapped_column(default=TeacherTitle.OTHER, comment="职称")
    position: Mapped[str] = mapped_column(String(50), nullable=False, comment="职务")
    gender: Mapped[str] = mapped_column(String(10), nullable=False, comment="性别")
    birth_date: Mapped[date] = mapped_column(Date, nullable=False, comment="出生日期")
    id_card: Mapped[str] = mapped_column(String(18), unique=True, nullable=False, comment="身份证号")
    phone: Mapped[Optional[str]] = mapped_column(String(20), comment="联系电话")
    email: Mapped[Optional[str]] = mapped_column(String(100), comment="电子邮箱")
    address: Mapped[Optional[str]] = mapped_column(String(200), comment="家庭住址")

    # 教师信息
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        comment="院系ID",
    )
    hire_date: Mapped[date] = mapped_column(Date, nullable=False, comment="入职日期")
    leave_date: Mapped[Optional[date]] = mapped_column(Date, comment="离职日期")
    education: Mapped[str] = mapped_column(String(50), nullable=False, comment="学历")
    degree: Mapped[str] = mapped_column(String(50), nullable=False, comment="学位")
    research_direction: Mapped[Optional[str]] = mapped_column(String(200), comment="研究方向")

    # 状态信息
    status: Mapped[TeacherStatus] = mapped_column(
        default=TeacherStatus.ACTIVE,
        nullable=False,
        index=True,
        comment="状态：在职、退休、离职",
    )
    is_full_time: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否全职")

    # 其他信息
    political_status: Mapped[Optional[str]] = mapped_column(String(20), comment="政治面貌")
    nationality: Mapped[Optional[str]] = mapped_column(String(20), comment="民族")
    native_place: Mapped[Optional[str]] = mapped_column(String(50), comment="籍贯")
    photo_url: Mapped[Optional[str]] = mapped_column(String(200), comment="照片URL")

    # 关联关系
    department: Mapped["Department"] = relationship("Department", back_populates="teachers", lazy="joined")
    managed_classes: Mapped[List["Classes"]] = relationship(
        "Classes",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="teacher", cascade="all, delete-orphan")
    teaching_plans: Mapped[List["TeachingPlan"]] = relationship(
        "TeachingPlan",
        foreign_keys="[TeachingPlan.teacher_id]",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    grades: Mapped[List["Grade"]] = relationship("Grade", back_populates="teacher", cascade="all, delete-orphan")
    course_materials: Mapped[List["CourseMaterial"]] = relationship(
        "CourseMaterial",
        foreign_keys="[CourseMaterial.uploader_id]",
        back_populates="uploader",
        cascade="all, delete-orphan",
    )
    title_records: Mapped[List["TeacherTitleRecord"]] = relationship(
        "TeacherTitleRecord",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    evaluation_rules: Mapped[List["EvaluationRule"]] = relationship(
        "EvaluationRule",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    evaluations: Mapped[List["EvaluationRecord"]] = relationship(
        "EvaluationRecord",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    attendances: Mapped[List["TeacherAttendance"]] = relationship(
        "TeacherAttendance",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    teacher_courses: Mapped[List["TeacherCourse"]] = relationship(
        "TeacherCourse",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_teachers_name_department",
            "name",
            "department_id",
        ),
        Index(
            "ix_teachers_status_department",
            "status",
            "department_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<Teacher {self.code} {self.name}>"


class TeacherTitleRecord(AbstractModel):
    """教师职称记录模型"""

    __tablename__ = "teacher_title_records"

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, comment="教师ID")
    title: Mapped[TeacherTitle] = mapped_column(nullable=False, comment="职称")
    certificate_no: Mapped[Optional[str]] = mapped_column(String(50), comment="证书编号")
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, comment="获得日期")
    issue_authority: Mapped[str] = mapped_column(String(100), nullable=False, comment="发证机构")
    status: Mapped[str] = mapped_column(String(20), default="active", comment="状态：active=有效,expired=已过期,revoked=已撤销")
    revoke_reason: Mapped[Optional[str]] = mapped_column(Text, comment="撤销原因")
    comments: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="title_records")


class TeachingPlan(AbstractModel):
    """教学计划模型"""

    __tablename__ = "teaching_plans"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="计划名称")
    semester: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="学期")
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment="学年")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="计划描述")
    objectives: Mapped[Optional[str]] = mapped_column(Text, comment="教学目标")
    requirements: Mapped[Optional[str]] = mapped_column(Text, comment="教学要求")

    # 状态信息
    status: Mapped[TeachingPlanStatus] = mapped_column(
        default=TeachingPlanStatus.DRAFT,
        nullable=False,
        index=True,
        comment="状态",
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, comment="审核意见")

    # 外键关联
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="课程ID",
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="教师ID",
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        comment="审批人ID",
    )

    # 关联关系
    course: Mapped["Course"] = relationship("Course", back_populates="teaching_plans", lazy="joined")
    teacher: Mapped["Teacher"] = relationship(
        "Teacher",
        foreign_keys="[TeachingPlan.teacher_id]",
        back_populates="teaching_plans",
        lazy="joined"
    )
    approver: Mapped[Optional["Teacher"]] = relationship(
        "Teacher",
        foreign_keys="[TeachingPlan.approver_id]",
        lazy="joined"
    )
    details: Mapped[List["TeachingPlanDetail"]] = relationship(
        "TeachingPlanDetail",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    schedules: Mapped[List["TeachingSchedule"]] = relationship(
        "TeachingSchedule",
        back_populates="plan",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_teaching_plans_course_semester",
            "course_id",
            "semester",
        ),
        Index(
            "ix_teaching_plans_status_teacher",
            "status",
            "teacher_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<TeachingPlan {self.name}>"


class TeachingPlanDetail(AbstractModel):
    """教学计划详情模型"""

    __tablename__ = "teaching_plan_details"

    # 基本信息
    week: Mapped[int] = mapped_column(Integer, nullable=False, comment="教学周次")
    hours: Mapped[int] = mapped_column(Integer, nullable=False, comment="课时数")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="教学内容")
    objectives: Mapped[str] = mapped_column(Text, nullable=False, comment="教学目标")
    methods: Mapped[Optional[str]] = mapped_column(Text, comment="教学方法")
    resources: Mapped[Optional[str]] = mapped_column(Text, comment="教学资源")
    assignments: Mapped[Optional[str]] = mapped_column(Text, comment="作业要求")
    key_points: Mapped[Optional[str]] = mapped_column(Text, comment="教学重点")
    difficulties: Mapped[Optional[str]] = mapped_column(Text, comment="教学难点")
    references: Mapped[Optional[str]] = mapped_column(Text, comment="参考资料")

    # 外键关联
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("teaching_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教学计划ID",
    )

    # 关联关系
    plan: Mapped["TeachingPlan"] = relationship("TeachingPlan", back_populates="details", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_teaching_plan_details_week",
            "plan_id",
            "week",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<TeachingPlanDetail Week {self.week}>"


class TeachingSchedule(AbstractModel):
    """教学进度模型"""

    __tablename__ = "teaching_schedules"

    # 基本信息
    actual_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="实际授课日期")
    actual_content: Mapped[str] = mapped_column(Text, nullable=False, comment="实际教学内容")
    completion_rate: Mapped[int] = mapped_column(Integer, nullable=False, comment="完成度（百分比）")
    status: Mapped[TeachingScheduleStatus] = mapped_column(
        default=TeachingScheduleStatus.PENDING,
        nullable=False,
        comment="状态",
    )
    delay_reason: Mapped[Optional[str]] = mapped_column(Text, comment="延期原因")
    adjustment: Mapped[Optional[str]] = mapped_column(Text, comment="调整说明")
    notes: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("teaching_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教学计划ID",
    )
    detail_id: Mapped[int] = mapped_column(
        ForeignKey("teaching_plan_details.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教学计划详情ID",
    )

    # 关联关系
    plan: Mapped["TeachingPlan"] = relationship("TeachingPlan", back_populates="schedules", lazy="joined")
    detail: Mapped["TeachingPlanDetail"] = relationship("TeachingPlanDetail", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_teaching_schedules_status_plan",
            "status",
            "plan_id",
        ),
        # {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<TeachingSchedule {self.actual_date} {self.status}>"


class TeacherCourse(AbstractModel):
    """教师课程记录模型"""

    __tablename__ = "teacher_courses"

    # 基本信息
    role: Mapped[TeacherRole] = mapped_column(default=TeacherRole.LECTURER, nullable=False, index=True, comment="教师角色")
    workload: Mapped[float] = mapped_column(Float(precision=2), nullable=False, comment="工作量")
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
        comment="状态：pending=待确认,confirmed=已确认,completed=已完成",
    )
    evaluation_score: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="评教分数")
    comments: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教师ID",
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

    # 关联关系
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="teacher_courses", lazy="joined")
    course: Mapped["Course"] = relationship("Course", back_populates="teacher_courses", lazy="joined")
    semester: Mapped["Semester"] = relationship("Semester", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_teacher_courses_unique",
            "teacher_id",
            "course_id",
            "semester_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<TeacherCourse {self.teacher.name} {self.course.name}>"


class TeacherAttendance(AbstractModel):
    """教师考勤记录模型"""

    __tablename__ = "teacher_attendances"

    # 基本信息
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="考勤日期")
    type: Mapped[TeacherAttendanceType] = mapped_column(nullable=False, index=True, comment="考勤类型")
    check_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="签到时间")
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="签退时间")
    leave_type: Mapped[Optional[TeacherLeaveType]] = mapped_column(comment="请假类型")
    leave_reason: Mapped[Optional[str]] = mapped_column(Text, comment="请假原因")
    location: Mapped[Optional[str]] = mapped_column(String(200), comment="考勤地点")
    device: Mapped[Optional[str]] = mapped_column(String(100), comment="考勤设备")

    # 审批信息
    approve_status: Mapped[TeacherAttendanceStatus] = mapped_column(
        default=TeacherAttendanceStatus.PENDING,
        nullable=False,
        index=True,
        comment="审批状态",
    )
    approve_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="审批时间")
    approve_comments: Mapped[Optional[str]] = mapped_column(Text, comment="审批意见")
    comments: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教师ID",
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="审批人ID",
    )

    # 关联关系
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="attendances", lazy="joined")
    approver: Mapped[Optional["User"]] = relationship("User", back_populates="approved_attendances", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_teacher_attendances_date_teacher",
            "date",
            "teacher_id",
            unique=True,
        ),
        Index(
            "ix_teacher_attendances_status_type",
            "approve_status",
            "type",
        ),
    )

    def __repr__(self) -> str:
        return f"<TeacherAttendance {self.teacher.name} {self.date:%Y-%m-%d}>"
