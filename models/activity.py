from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class ActivityType(str, PyEnum):
    """活动类型"""

    ACADEMIC = "academic"  # 学术活动
    SPORTS = "sports"  # 体育活动
    ARTS = "arts"  # 艺术活动
    SOCIAL = "social"  # 社交活动
    COMPETITION = "competition"  # 竞赛活动
    CELEBRATION = "celebration"  # 庆祝活动
    VOLUNTEER = "volunteer"  # 志愿活动
    CLUB = "club"  # 社团活动
    LECTURE = "lecture"  # 讲座活动
    WORKSHOP = "workshop"  # 工作坊
    OTHER = "other"  # 其他活动


class ActivityStatus(str, PyEnum):
    """活动状态"""

    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消
    ONGOING = "ongoing"  # 进行中
    COMPLETED = "completed"  # 已完成
    ARCHIVED = "archived"  # 已归档


class ParticipantStatus(str, PyEnum):
    """参与状态"""

    REGISTERED = "registered"  # 已报名
    CONFIRMED = "confirmed"  # 已确认
    WAITLISTED = "waitlisted"  # 候补
    CANCELLED = "cancelled"  # 已取消
    ATTENDED = "attended"  # 已参加
    ABSENT = "absent"  # 缺席


class Activity(AbstractModel):
    """活动模型"""

    __tablename__ = "activities"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="活动标题")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="活动描述")
    type: Mapped[ActivityType] = mapped_column(nullable=False, index=True, comment="活动类型")
    status: Mapped[ActivityStatus] = mapped_column(
        default=ActivityStatus.DRAFT, nullable=False, index=True, comment="活动状态"
    )

    # 时间地点
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="结束时间")
    location: Mapped[str] = mapped_column(String(200), nullable=False, comment="活动地点")
    venue: Mapped[Optional[str]] = mapped_column(String(100), comment="具体场地")
    registration_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="报名截止时间")

    # 参与信息
    max_participants: Mapped[Optional[int]] = mapped_column(Integer, comment="最大参与人数")
    min_participants: Mapped[Optional[int]] = mapped_column(Integer, comment="最小参与人数")
    current_participants: Mapped[int] = mapped_column(Integer, default=0, comment="当前参与人数")
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否公开")
    need_approval: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否需要审批")

    # 活动详情
    requirements: Mapped[Optional[str]] = mapped_column(Text, comment="参与要求")
    schedule: Mapped[Optional[str]] = mapped_column(Text, comment="活动日程")
    materials: Mapped[Optional[str]] = mapped_column(Text, comment="所需材料")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")
    budget: Mapped[Optional[str]] = mapped_column(Text, comment="活动预算")
    contact: Mapped[Optional[str]] = mapped_column(String(100), comment="联系方式")

    # 外键关联
    organizer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="组织者ID",
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        comment="所属部门ID",
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="审批人ID",
    )

    # 关联关系
    organizer: Mapped["User"] = relationship("User", foreign_keys=[organizer_id], lazy="joined")
    department: Mapped[Optional["Department"]] = relationship("Department", lazy="joined")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approver_id], lazy="joined")
    participants: Mapped[List["ActivityParticipant"]] = relationship(
        "ActivityParticipant", back_populates="activity", cascade="all, delete-orphan"
    )
    announcements: Mapped[List["ActivityAnnouncement"]] = relationship(
        "ActivityAnnouncement", back_populates="activity", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_activities_type_status",
            "type",
            "status",
        ),
        Index(
            "ix_activities_time_range",
            "start_time",
            "end_time",
        ),
        Index(
            "ix_activities_department",
            "department_id",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Activity {self.title}>"


class ActivityParticipant(AbstractModel):
    """活动参与者模型"""

    __tablename__ = "activity_participants"

    # 基本信息
    status: Mapped[ParticipantStatus] = mapped_column(
        default=ParticipantStatus.REGISTERED,
        nullable=False,
        index=True,
        comment="参与状态",
    )
    registration_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment="报名时间",
    )
    confirm_time: Mapped[Optional[datetime]] = mapped_column(comment="确认时间")
    cancel_time: Mapped[Optional[datetime]] = mapped_column(comment="取消时间")
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, comment="取消原因")
    check_in_time: Mapped[Optional[datetime]] = mapped_column(comment="签到时间")
    check_out_time: Mapped[Optional[datetime]] = mapped_column(comment="签退时间")
    feedback: Mapped[Optional[str]] = mapped_column(Text, comment="参与反馈")

    # 外键关联
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="活动ID",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="参与者ID",
    )

    # 关联关系
    activity: Mapped["Activity"] = relationship(
        "Activity",
        back_populates="participants",
        lazy="joined",
    )
    user: Mapped["User"] = relationship("User", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_activity_participants_unique",
            "activity_id",
            "user_id",
            unique=True,
        ),
        Index(
            "ix_activity_participants_status",
            "status",
            "activity_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<ActivityParticipant {self.user.name} {self.status}>"


class ActivityAnnouncement(AbstractModel):
    """活动通知模型"""

    __tablename__ = "activity_announcements"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="通知标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="通知内容")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否置顶")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")

    # 外键关联
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="活动ID",
    )
    publisher_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="发布者ID",
    )

    # 关联关系
    activity: Mapped["Activity"] = relationship(
        "Activity",
        back_populates="announcements",
        lazy="joined",
    )
    publisher: Mapped["User"] = relationship("User", lazy="joined")
    receipt_records: Mapped[List["AnnouncementReceipt"]] = relationship(
        "AnnouncementReceipt",
        back_populates="announcement",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_activity_announcements_priority",
            "activity_id",
            "priority",
            "is_pinned",
        ),
    )

    def __repr__(self) -> str:
        return f"<ActivityAnnouncement {self.title}>"


class AnnouncementReceipt(AbstractModel):
    """通知接收记录模型"""

    __tablename__ = "announcement_receipts"

    # 基本信息
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否已读")
    read_time: Mapped[Optional[datetime]] = mapped_column(comment="阅读时间")
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否标星")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否删除")
    delete_time: Mapped[Optional[datetime]] = mapped_column(comment="删除时间")

    # 外键关联
    announcement_id: Mapped[int] = mapped_column(
        ForeignKey("activity_announcements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="通知ID",
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="接收者ID",
    )

    # 关联关系
    announcement: Mapped["ActivityAnnouncement"] = relationship(
        "ActivityAnnouncement",
        back_populates="receipt_records",
        lazy="joined",
    )
    recipient: Mapped["User"] = relationship("User", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_announcement_receipts_unique",
            "announcement_id",
            "recipient_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<AnnouncementReceipt {self.recipient.name} {self.is_read}>"
