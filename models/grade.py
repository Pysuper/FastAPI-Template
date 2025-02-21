from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class GradeStatus(str, PyEnum):
    """成绩状态"""

    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审核
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 已归档
    CANCELLED = "cancelled"  # 已取消


class GradeItemType(str, PyEnum):
    """成绩项目类型"""

    HOMEWORK = "homework"  # 作业
    QUIZ = "quiz"  # 小测
    MIDTERM = "midterm"  # 期中考试
    FINAL = "final"  # 期末考试
    PRACTICE = "practice"  # 实践
    ATTENDANCE = "attendance"  # 考勤
    OTHER = "other"  # 其他


class GradeLevel(str, PyEnum):
    """成绩等级"""

    A_PLUS = "A+"  # 95-100
    A = "A"  # 90-94
    A_MINUS = "A-"  # 85-89
    B_PLUS = "B+"  # 82-84
    B = "B"  # 78-81
    B_MINUS = "B-"  # 75-77
    C_PLUS = "C+"  # 72-74
    C = "C"  # 68-71
    C_MINUS = "C-"  # 65-67
    D = "D"  # 60-64
    F = "F"  # 0-59


class Grade(AbstractModel):
    """成绩模型"""

    __tablename__ = "grades"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="成绩名称")
    semester: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="学期")
    grading_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, comment="评分日期")

    # 成绩组成部分
    attendance_score: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="考勤成绩")
    homework_score: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="作业成绩")
    midterm_score: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="期中成绩")
    final_score: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="期末成绩")
    total_score: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="总评成绩")
    grade_point: Mapped[Optional[float]] = mapped_column(Float(precision=1), comment="绩点")
    grade_level: Mapped[Optional[GradeLevel]] = mapped_column(comment="等级")

    # 成绩状态
    status: Mapped[GradeStatus] = mapped_column(default=GradeStatus.DRAFT, nullable=False, index=True, comment="状态")
    is_makeup: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否补考")
    is_retake: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否重修")

    # 成绩备注
    notes: Mapped[Optional[str]] = mapped_column(Text, comment="备注")
    review_notes: Mapped[Optional[str]] = mapped_column(Text, comment="审核意见")

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
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="教师ID",
    )
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("semesters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="学期ID",
    )
    rule_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("grade_rules.id", ondelete="SET NULL"),
        comment="成绩规则ID",
    )

    # 关联关系
    student: Mapped["Student"] = relationship("Student", back_populates="grades", lazy="joined")
    course: Mapped["Course"] = relationship("Course", back_populates="grades", lazy="joined")
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="grades", lazy="joined")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="grades", lazy="joined")
    rule: Mapped[Optional["GradeRule"]] = relationship("GradeRule", back_populates="grades", lazy="joined")
    items: Mapped[List["GradeItem"]] = relationship("GradeItem", back_populates="grade", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index(
            "ix_grades_student_course_semester",
            "student_id",
            "course_id",
            "semester_id",
            unique=True,
        ),
        Index(
            "ix_grades_status_teacher",
            "status",
            "teacher_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<Grade {self.student.name} {self.course.name} {self.total_score}>"


class GradeRule(AbstractModel):
    """成绩规则模型"""

    __tablename__ = "grade_rules"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="规则名称")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="规则描述")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="版本号")

    # 成绩比例
    attendance_weight: Mapped[float] = mapped_column(Float(precision=2), nullable=False, default=0.1, comment="考勤成绩比例")
    homework_weight: Mapped[float] = mapped_column(Float(precision=2), nullable=False, default=0.2, comment="作业成绩比例")
    midterm_weight: Mapped[float] = mapped_column(Float(precision=2), nullable=False, default=0.3, comment="期中成绩比例")
    final_weight: Mapped[float] = mapped_column(Float(precision=2), nullable=False, default=0.4, comment="期末成绩比例")

    # 及格线
    pass_score: Mapped[float] = mapped_column(Float(precision=1), nullable=False, default=60.0, comment="及格分数线")

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="是否启用")
    effective_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, comment="生效日期")

    # 外键关联
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="课程ID",
    )

    # 关联关系
    course: Mapped["Course"] = relationship("Course", back_populates="grade_rules", lazy="joined")
    grades: Mapped[List["Grade"]] = relationship("Grade", back_populates="rule", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (Index("ix_grade_rules_course_version", "course_id", "version", unique=True),)

    def __repr__(self) -> str:
        return f"<GradeRule {self.name} v{self.version}>"


class GradeItem(AbstractModel):
    """成绩项目模型"""

    __tablename__ = "grade_items"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="项目名称")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="项目描述")
    score: Mapped[float] = mapped_column(Float(precision=2), nullable=False, comment="分数")
    weight: Mapped[float] = mapped_column(Float(precision=2), nullable=False, comment="权重")
    type: Mapped[GradeItemType] = mapped_column(nullable=False, index=True, comment="类型")
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="序号")
    due_date: Mapped[Optional[datetime]] = mapped_column(comment="截止日期")
    grading_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, comment="评分日期")

    # 外键关联
    grade_id: Mapped[int] = mapped_column(
        ForeignKey("grades.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="成绩ID",
    )

    # 关联关系
    grade: Mapped["Grade"] = relationship("Grade", back_populates="items", lazy="joined")

    # 索引
    __table_args__ = (
        Index(
            "ix_grade_items_type_grade",
            "type",
            "grade_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<GradeItem {self.name} {self.score}>"
