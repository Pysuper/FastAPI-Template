from datetime import time, datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import ForeignKey, String, Time, Text, Integer, Index, Table, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel
from models.attendance import Attendance, AttendanceRule
from models.enrollment import EnrollmentRule
from models.evaluation import EvaluationRule, EvaluationRecord
from models.exam import Exam
from models.grade import Grade, GradeRule
from models.teacher import TeachingPlan, TeacherCourse

# 课程-教师关联表
courses_teachers = Table(
    "courses_teachers",
    AbstractModel.metadata,
    Column("course_id", Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("teacher_id", Integer, ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.now, nullable=False),
    Index("ix_courses_teachers_course", "course_id"),
    Index("ix_courses_teachers_teacher", "teacher_id"),
)

class CourseStatus(str, PyEnum):
    """课程状态"""

    DRAFT = "draft"  # 草稿
    ACTIVE = "active"  # 已激活
    INACTIVE = "inactive"  # 未激活
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除


class CourseType(str, PyEnum):
    """课程类型"""

    REQUIRED = "required"  # 必修课
    ELECTIVE = "elective"  # 选修课
    OPTIONAL = "optional"  # 任选课
    PRACTICE = "practice"  # 实践课


class Course(AbstractModel):
    """课程信息模型"""

    __tablename__ = "courses"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="课程名称")
    type: Mapped[CourseType] = mapped_column(default=CourseType.REQUIRED, comment="课程类型")
    credits: Mapped[int] = mapped_column(Integer, nullable=False, comment="学分")
    hours: Mapped[int] = mapped_column(Integer, nullable=False, comment="课时")
    max_students: Mapped[int] = mapped_column(Integer, default=100, comment="最大学生数")
    min_students: Mapped[int] = mapped_column(Integer, default=1, comment="最小学生数")
    prerequisites: Mapped[Optional[str]] = mapped_column(Text, comment="先修课程要求")
    objectives: Mapped[Optional[str]] = mapped_column(Text, comment="课程目标")
    outline: Mapped[Optional[str]] = mapped_column(Text, comment="课程大纲")
    evaluation_method: Mapped[Optional[str]] = mapped_column(Text, comment="考核方式")

    # 状态信息
    status: Mapped[CourseStatus] = mapped_column(default=CourseStatus.DRAFT, nullable=False, index=True, comment="课程状态")

    # 教师关联
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, comment="主讲教师ID"
    )
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="courses", lazy="joined")

    # 专业关联
    major_id: Mapped[int] = mapped_column(
        ForeignKey("majors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="专业ID",
    )
    semester_id: Mapped[int] = mapped_column(
        ForeignKey("semesters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="学期ID",
    )

    # 关联关系
    major: Mapped["Major"] = relationship("Major", back_populates="courses", lazy="joined")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="courses", lazy="joined")
    teachers: Mapped[List["Teacher"]] = relationship(
        "Teacher",
        secondary=courses_teachers,
        back_populates="courses",
        lazy="joined",
    )
    materials: Mapped[List["CourseMaterial"]] = relationship(
        "CourseMaterial", back_populates="course", cascade="all, delete-orphan"
    )
    schedules: Mapped[List["CourseSchedule"]] = relationship(
        "CourseSchedule", back_populates="course", cascade="all, delete-orphan"
    )
    enrollments: Mapped[List["CourseEnrollment"]] = relationship(
        "CourseEnrollment", back_populates="course", cascade="all, delete-orphan"
    )
    grades: Mapped[List["Grade"]] = relationship("Grade", back_populates="course", cascade="all, delete-orphan")
    grade_rules: Mapped[List["GradeRule"]] = relationship(
        "GradeRule", back_populates="course", cascade="all, delete-orphan"
    )
    teaching_plans: Mapped[List["TeachingPlan"]] = relationship(
        "TeachingPlan", back_populates="course", cascade="all, delete-orphan"
    )
    teacher_courses: Mapped[List["TeacherCourse"]] = relationship(
        "TeacherCourse", back_populates="course", cascade="all, delete-orphan"
    )
    enrollment_rules: Mapped[List["EnrollmentRule"]] = relationship(
        "EnrollmentRule", back_populates="course", cascade="all, delete-orphan"
    )
    evaluation_rules: Mapped[List["EvaluationRule"]] = relationship(
        "EvaluationRule", back_populates="course", cascade="all, delete-orphan"
    )
    evaluations: Mapped[List["EvaluationRecord"]] = relationship(
        "EvaluationRecord", back_populates="course", cascade="all, delete-orphan"
    )
    exams: Mapped[List["Exam"]] = relationship(
        "Exam",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    attendance_rules: Mapped[List["AttendanceRule"]] = relationship(
        "AttendanceRule",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index("ix_courses_name_major", "name", "major_id"),
        Index("ix_courses_status_teacher", "status", "teacher_id"),
    )

    def __repr__(self) -> str:
        return f"<Course {self.code} {self.name}>"


class CourseMaterial(AbstractModel):
    """课程资料模型"""

    __tablename__ = "course_materials"

    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True, comment="资料标题")
    type: Mapped[str] = mapped_column(String(50), nullable=False, comment="资料类型")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件路径")
    file_size: Mapped[Optional[int]] = mapped_column(Integer, comment="文件大小(字节)")
    file_type: Mapped[Optional[str]] = mapped_column(String(50), comment="文件类型")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="资料描述")
    download_count: Mapped[int] = mapped_column(Integer, default=0, comment="下载次数")

    # 外键关联
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID"
    )
    uploader_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True, index=True, comment="上传者ID"
    )

    # 关联关系
    course: Mapped["Course"] = relationship("Course", back_populates="materials", lazy="joined")
    uploader: Mapped[Optional["Teacher"]] = relationship("Teacher", back_populates="course_materials", lazy="joined")

    def __repr__(self) -> str:
        return f"<CourseMaterial {self.title}>"


class CourseSchedule(AbstractModel):
    """课程安排模型"""

    __tablename__ = "course_schedules"

    # 基本信息
    classroom: Mapped[str] = mapped_column(String(50), nullable=False, comment="教室")
    building: Mapped[str] = mapped_column(String(50), nullable=False, comment="教学楼")
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, comment="星期几(1-7)")
    start_time: Mapped[time] = mapped_column(Time, nullable=False, comment="上课时间")
    end_time: Mapped[time] = mapped_column(Time, nullable=False, comment="下课时间")
    semester: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="学期")
    week_start: Mapped[int] = mapped_column(Integer, nullable=False, comment="起始周")
    week_end: Mapped[int] = mapped_column(Integer, nullable=False, comment="结束周")

    # 外键关联
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID"
    )

    # 关联关系
    course: Mapped["Course"] = relationship("Course", back_populates="schedules", lazy="joined")

    # 索引
    __table_args__ = (Index("ix_course_schedules_time", "semester", "day_of_week", "start_time", "end_time"),)

    def __repr__(self) -> str:
        return f"<CourseSchedule {self.course.name} {self.day_of_week} {self.start_time}-{self.end_time}>"
