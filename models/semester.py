# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：semester.py
@Author  ：PySuper
@Date    ：2024/12/30 17:03 
@Desc    ：Speedy semester.py
"""

from datetime import date
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import String, Date, Text, Integer, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class SemesterStatus(str, PyEnum):
    """学期状态"""

    UPCOMING = "upcoming"  # 即将开始
    ONGOING = "ongoing"  # 进行中
    ENDED = "ended"  # 已结束
    ARCHIVED = "archived"  # 已归档


class SemesterType(str, PyEnum):
    """学期类型"""

    SPRING = "spring"  # 春季学期
    SUMMER = "summer"  # 夏季学期
    AUTUMN = "autumn"  # 秋季学期
    WINTER = "winter"  # 冬季学期


class Semester(AbstractModel):
    """学期模型"""

    __tablename__ = "semesters"

    # 基本信息
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="学期名称")
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="学期编码")
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="学年")
    type: Mapped[SemesterType] = mapped_column(default=SemesterType.SPRING, nullable=False, index=True, comment="学期类型")

    # 时间信息
    start_date: Mapped[date] = mapped_column(Date, nullable=False, comment="开始日期")
    end_date: Mapped[date] = mapped_column(Date, nullable=False, comment="结束日期")
    registration_start_date: Mapped[Optional[date]] = mapped_column(Date, comment="注册开始日期")
    registration_end_date: Mapped[Optional[date]] = mapped_column(Date, comment="注册结束日期")
    course_selection_start_date: Mapped[Optional[date]] = mapped_column(Date, comment="选课开始日期")
    course_selection_end_date: Mapped[Optional[date]] = mapped_column(Date, comment="选课结束日期")
    grade_submission_start_date: Mapped[Optional[date]] = mapped_column(Date, comment="成绩提交开始日期")
    grade_submission_end_date: Mapped[Optional[date]] = mapped_column(Date, comment="成绩提交结束日期")

    # 状态信息
    status: Mapped[SemesterStatus] = mapped_column(
        default=SemesterStatus.UPCOMING, nullable=False, index=True, comment="状态"
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否当前学期")

    # 其他信息
    description: Mapped[Optional[str]] = mapped_column(Text, comment="学期描述")
    total_weeks: Mapped[int] = mapped_column(Integer, default=16, comment="总周数")
    vacation_weeks: Mapped[Optional[str]] = mapped_column(String(100), comment="假期周数")
    notes: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="semester",
        cascade="all, delete-orphan"
    )
    enrollments: Mapped[List["CourseEnrollment"]] = relationship(
        "CourseEnrollment",
        back_populates="semester",
        cascade="all, delete-orphan"
    )
    grades: Mapped[List["Grade"]] = relationship(
        "Grade",
        back_populates="semester",
        cascade="all, delete-orphan"
    )
    enrollment_periods: Mapped[List["EnrollmentPeriod"]] = relationship(
        "EnrollmentPeriod",
        back_populates="semester",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_semesters_year_type",
            "year",
            "type",
            unique=True,
        ),
        Index(
            "ix_semesters_status_current",
            "status",
            "is_current",
        ),
        Index(
            "ix_semesters_date_range",
            "start_date",
            "end_date",
        ),
    )

    def __repr__(self) -> str:
        return f"<Semester {self.code} {self.name}>"
