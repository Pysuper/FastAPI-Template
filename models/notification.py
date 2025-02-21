from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class NotificationType(str, PyEnum):
    """通知类型"""

    ANNOUNCEMENT = "announcement"  # 公告
    HOMEWORK = "homework"  # 作业
    EXAM = "exam"  # 考试
    ATTENDANCE = "attendance"  # 考勤
    BEHAVIOR = "behavior"  # 行为
    GRADE = "grade"  # 成绩
    ACTIVITY = "activity"  # 活动
    EMERGENCY = "emergency"  # 紧急
    OTHER = "other"  # 其他


class FeedbackStatus(str, PyEnum):
    """反馈状态"""

    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    REPLIED = "replied"  # 已回复
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭


class ParentFeedback(AbstractModel):
    """家长反馈模型"""

    __tablename__ = "parent_feedbacks"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="反馈标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="反馈内容")
    status: Mapped[FeedbackStatus] = mapped_column(
        default=FeedbackStatus.PENDING,
        nullable=False,
        index=True,
        comment="处理状态",
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    category: Mapped[str] = mapped_column(String(50), nullable=False, comment="反馈类别")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")

    # 处理信息
    handler_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), comment="处理人ID")
    handle_time: Mapped[Optional[datetime]] = mapped_column(comment="处理时间")
    handle_result: Mapped[Optional[str]] = mapped_column(Text, comment="处理结果")
    close_time: Mapped[Optional[datetime]] = mapped_column(comment="关闭时间")
    close_reason: Mapped[Optional[str]] = mapped_column(Text, comment="关闭原因")

    # 外键关联
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("parents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="家长ID",
    )

    # 关联关系
    parent: Mapped["Parent"] = relationship(
        "Parent",
        back_populates="feedbacks",
        lazy="joined",
    )
    handler: Mapped[Optional["User"]] = relationship("User", lazy="joined")
    replies: Mapped[List["FeedbackReply"]] = relationship(
        "FeedbackReply",
        back_populates="feedback",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_parent_feedbacks_status_priority",
            "status",
            "priority",
        ),
    )

    def __repr__(self) -> str:
        return f"<ParentFeedback {self.title}>"


class FeedbackReply(AbstractModel):
    """反馈回复模型"""

    __tablename__ = "feedback_replies"

    # 基本信息
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="回复内容")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否内部回复")

    # 外键关联
    feedback_id: Mapped[int] = mapped_column(
        ForeignKey("parent_feedbacks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="反馈ID",
    )
    replier_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="回复人ID",
    )

    # 关联关系
    feedback: Mapped["ParentFeedback"] = relationship(
        "ParentFeedback",
        back_populates="replies",
        lazy="joined",
    )
    replier: Mapped["User"] = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        return f"<FeedbackReply {self.replier.name}>"


class Notification(AbstractModel):
    """通知模型"""

    __tablename__ = "notifications"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="通知标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="通知内容")
    type: Mapped[NotificationType] = mapped_column(nullable=False, index=True, comment="通知类型")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否草稿")
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已发送")
    send_time: Mapped[Optional[datetime]] = mapped_column(comment="发送时间")

    # 目标信息
    target_grade: Mapped[Optional[int]] = mapped_column(Integer, comment="目标年级")
    target_class: Mapped[Optional[int]] = mapped_column(Integer, comment="目标班级")
    target_students: Mapped[Optional[str]] = mapped_column(Text, comment="目标学生")
    target_parents: Mapped[Optional[str]] = mapped_column(Text, comment="目标家长")

    # 外键关联
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="发送人ID",
    )

    # 关联关系
    sender: Mapped["User"] = relationship("User", lazy="joined")
    notification_records: Mapped[List["NotificationRecord"]] = relationship(
        "NotificationRecord",
        back_populates="notification",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_notifications_type_priority",
            "type",
            "priority",
        ),
        Index(
            "ix_notifications_send_time",
            "send_time",
            "is_sent",
        ),
    )

    def __repr__(self) -> str:
        return f"<Notification {self.title}>"


class NotificationRecord(AbstractModel):
    """通知记录模型"""

    __tablename__ = "notification_records"

    # 基本信息
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否已读")
    read_time: Mapped[Optional[datetime]] = mapped_column(comment="阅读时间")
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否标星")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否删除")
    delete_time: Mapped[Optional[datetime]] = mapped_column(comment="删除时间")

    # 外键关联
    notification_id: Mapped[int] = mapped_column(
        ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True, comment="通知ID"
    )
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True, comment="家长ID"
    )

    # 关联关系
    notification: Mapped["Notification"] = relationship(
        "Notification", back_populates="notification_records", lazy="joined"
    )
    parent: Mapped["Parent"] = relationship("Parent", back_populates="notification_records", lazy="joined")

    # 索引
    __table_args__ = (Index("ix_notification_records_unique", "notification_id", "parent_id", unique=True),)

    def __repr__(self) -> str:
        return f"<NotificationRecord {self.notification.title} {self.parent.name}>"
