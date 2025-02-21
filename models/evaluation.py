from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    JSON,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Float,
    Index,
    MetaData,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


# 创建metadata并设置命名约定
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class IndicatorType(str, PyEnum):
    """评价指标类型"""

    TEACHING = "teaching"  # 教学态度
    CONTENT = "content"  # 教学内容
    INTERACTION = "interaction"  # 教学互动
    EFFECT = "effect"  # 教学效果
    PREPARATION = "preparation"  # 教学准备
    MATERIAL = "material"  # 教学资料
    ASSIGNMENT = "assignment"  # 作业批改
    GUIDANCE = "guidance"  # 课外辅导
    OTHER = "other"  # 其他


class EvaluationStatus(str, PyEnum):
    """评教状态"""

    DRAFT = "draft"  # 草稿
    SUBMITTED = "submitted"  # 已提交
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消


class EvaluationTargetType(str, PyEnum):
    """评教对象类型"""

    COURSE = "course"  # 课程
    TEACHER = "teacher"  # 教师
    TEACHING = "teaching"  # 教学
    MATERIAL = "material"  # 教材


class EvaluationIndicator(AbstractModel):
    """教学评价指标模型"""

    __tablename__ = "evaluation_indicators"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="指标ID")
    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="指标名称")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="指标描述")
    type: Mapped[IndicatorType] = mapped_column(nullable=False, index=True, comment="指标类型")

    # 评分规则
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0, comment="权重")
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100, comment="最高分")
    min_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="最低分")
    step: Mapped[float] = mapped_column(Float, default=1.0, comment="评分步长")
    scoring_criteria: Mapped[Optional[str]] = mapped_column(Text, comment="评分标准")

    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否必填")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    evaluations: Mapped[List["EvaluationRecord"]] = relationship(
        "EvaluationRecord",
        back_populates="indicator",
        cascade="all, delete-orphan",
    )

    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("evaluation_indicators.id"), nullable=True, comment="父级指标ID"
    )
    parent: Mapped[Optional["EvaluationIndicator"]] = relationship(
        "EvaluationIndicator",
        remote_side=[id],
        back_populates="children",
        uselist=False,
    )
    children: Mapped[List["EvaluationIndicator"]] = relationship(
        "EvaluationIndicator",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_evaluation_indicators_type_active",
            "type",
            "is_active",
        ),
        Index(
            "ix_evaluation_indicators_priority",
            "priority",
            "is_active",
        ),
        # {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<EvaluationIndicator {self.name}>"


class EvaluationRule(AbstractModel):
    """教学评价规则模型"""

    __tablename__ = "evaluation_rules"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="规则名称")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="规则描述")
    target_type: Mapped[EvaluationTargetType] = mapped_column(nullable=False, index=True, comment="评价对象类型")

    # 评价时间限制
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="结束时间")
    remind_days: Mapped[int] = mapped_column(Integer, default=3, comment="提醒提前天数")

    # 评价要求
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否必须评价")
    min_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="最少字数要求")
    allow_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否允许匿名")
    allow_modify: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否允许修改")
    need_approval: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否需要审核")

    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        index=True,
        comment="课程ID",
    )
    teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"),
        index=True,
        comment="教师ID",
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建人ID",
    )

    # 关联关系
    course: Mapped[Optional["Course"]] = relationship(
        "Course",
        back_populates="evaluation_rules",
        lazy="joined",
    )
    teacher: Mapped[Optional["Teacher"]] = relationship(
        "Teacher",
        back_populates="evaluation_rules",
        lazy="joined",
    )
    creator: Mapped["User"] = relationship("User", lazy="joined")
    evaluations: Mapped[List["EvaluationRecord"]] = relationship(
        "EvaluationRecord",
        back_populates="rule",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_evaluation_rules_target_active",
            "target_type",
            "is_active",
        ),
        Index(
            "ix_evaluation_rules_date_range",
            "start_date",
            "end_date",
        ),
        # {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<EvaluationRule {self.name}>"


class EvaluationRecord(AbstractModel):
    """教学评价记录模型"""

    __tablename__ = "evaluation_records"

    # 基本信息
    score: Mapped[int] = mapped_column(Integer, nullable=False, comment="评分")
    comment: Mapped[Optional[str]] = mapped_column(Text, comment="评价内容")
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否匿名")
    attachments: Mapped[Optional[str]] = mapped_column(Text, comment="附件")

    # 状态信息
    status: Mapped[EvaluationStatus] = mapped_column(
        default=EvaluationStatus.DRAFT, nullable=False, index=True, comment="状态"
    )

    # 评价时间
    submit_time: Mapped[Optional[datetime]] = mapped_column(comment="提交时间")
    review_time: Mapped[Optional[datetime]] = mapped_column(comment="审核时间")
    review_comments: Mapped[Optional[str]] = mapped_column(Text, comment="审核意见")

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
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="教师ID",
    )
    indicator_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_indicators.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="指标ID",
    )
    rule_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_rules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="规则ID",
    )
    reviewer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="审核人ID",
    )

    # 关联关系
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="evaluations",
        lazy="joined",
    )
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="evaluations",
        lazy="joined",
    )
    teacher: Mapped["Teacher"] = relationship(
        "Teacher",
        back_populates="evaluations",
        lazy="joined",
    )
    indicator: Mapped["EvaluationIndicator"] = relationship(
        "EvaluationIndicator",
        back_populates="evaluations",
        lazy="joined",
    )
    rule: Mapped["EvaluationRule"] = relationship(
        "EvaluationRule",
        back_populates="evaluations",
        lazy="joined",
    )
    reviewer: Mapped[Optional["User"]] = relationship("User", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_evaluation_records_student_course",
            "student_id",
            "course_id",
        ),
        Index(
            "ix_evaluation_records_teacher_indicator",
            "teacher_id",
            "indicator_id",
        ),
        Index(
            "ix_evaluation_records_status_rule",
            "status",
            "rule_id",
        ),
        # {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<EvaluationRecord {self.student.name} {self.teacher.name} {self.score}>"
