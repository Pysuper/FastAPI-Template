from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class AttendanceType(str, PyEnum):
    """考勤类型"""

    NORMAL = "normal"  # 正常
    LATE = "late"  # 迟到
    EARLY = "early"  # 早退
    ABSENT = "absent"  # 缺勤
    LEAVE = "leave"  # 请假


class AttendanceStatus(str, PyEnum):
    """考勤状态"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已驳回
    CANCELLED = "cancelled"  # 已取消


class LeaveType(str, PyEnum):
    """请假类型"""

    SICK = "sick"  # 病假
    PERSONAL = "personal"  # 事假
    OFFICIAL = "official"  # 公假
    EMERGENCY = "emergency"  # 紧急事假
    OTHER = "other"  # 其他


class Attendance(AbstractModel):
    """考勤记录模型"""

    __tablename__ = "attendances"

    # 基本信息
    type: Mapped[AttendanceType] = mapped_column(
        default=AttendanceType.NORMAL,
        nullable=False,
        index=True,
        comment="考勤类型",
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        default=AttendanceStatus.PENDING,
        nullable=False,
        index=True,
        comment="考勤状态",
    )
    date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        comment="考勤日期",
    )

    # 考勤时间
    check_in_time: Mapped[Optional[datetime]] = mapped_column(comment="签到时间")
    check_out_time: Mapped[Optional[datetime]] = mapped_column(comment="签退时间")
    late_minutes: Mapped[Optional[int]] = mapped_column(Integer, comment="迟到分钟数")
    early_minutes: Mapped[Optional[int]] = mapped_column(Integer, comment="早退分钟数")

    # 请假信息
    leave_type: Mapped[Optional[LeaveType]] = mapped_column(comment="请假类型")
    leave_reason: Mapped[Optional[str]] = mapped_column(Text, comment="请假原因")
    leave_start_time: Mapped[Optional[datetime]] = mapped_column(comment="请假开始时间")
    leave_end_time: Mapped[Optional[datetime]] = mapped_column(comment="请假结束时间")
    leave_attachments: Mapped[Optional[str]] = mapped_column(Text, comment="请假附件")

    # 审批信息
    approve_time: Mapped[Optional[datetime]] = mapped_column(comment="审批时间")
    approve_comments: Mapped[Optional[str]] = mapped_column(Text, comment="审批意见")
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否有效")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

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
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        comment="审批人ID",
    )

    # 关联关系
    student: Mapped["Student"] = relationship("Student", back_populates="attendances", lazy="joined")
    course: Mapped["Course"] = relationship("Course", back_populates="attendances", lazy="joined")
    approver: Mapped[Optional["Teacher"]] = relationship("Teacher", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_attendances_student_date",
            "student_id",
            "date",
        ),
        Index(
            "ix_attendances_course_date",
            "course_id",
            "date",
        ),
        Index(
            "ix_attendances_type_status",
            "type",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Attendance {self.student.name} {self.type} {self.date:%Y-%m-%d}>"


class AttendanceRule(AbstractModel):
    """考勤规则模型"""

    __tablename__ = "attendance_rules"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="规则名称")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="规则描述")

    # 考勤时间规则
    start_time: Mapped[str] = mapped_column(String(5), nullable=False, comment="开始时间，格式：HH:MM")
    end_time: Mapped[str] = mapped_column(String(5), nullable=False, comment="结束时间，格式：HH:MM")
    effective_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="生效日期")
    expire_date: Mapped[Optional[datetime]] = mapped_column(comment="失效日期")

    # 考勤阈值
    late_threshold: Mapped[int] = mapped_column(Integer, default=15, comment="迟到阈值（分钟）")
    early_threshold: Mapped[int] = mapped_column(Integer, default=15, comment="早退阈值（分钟）")
    absence_threshold: Mapped[int] = mapped_column(Integer, default=30, comment="缺勤阈值（分钟）")

    # 考勤要求
    require_location: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否要求位置")
    allowed_distance: Mapped[Optional[int]] = mapped_column(Integer, comment="允许的距离范围(米)")
    require_photo: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否要求照片")
    require_wifi: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否要求WiFi")
    allowed_wifi_list: Mapped[Optional[str]] = mapped_column(Text, comment="允许的WiFi列表")

    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="课程ID",
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建人ID",
    )

    # 关联关系
    course: Mapped["Course"] = relationship("Course", back_populates="attendance_rules", lazy="joined")
    creator: Mapped["Teacher"] = relationship("Teacher", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_attendance_rules_course_active",
            "course_id",
            "is_active",
        ),
        Index(
            "ix_attendance_rules_priority",
            "priority",
            "is_active",
        ),
    )

    def __repr__(self) -> str:
        return f"<AttendanceRule {self.name}>"
