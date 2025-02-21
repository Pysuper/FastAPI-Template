from datetime import datetime, date
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import BigInteger, Column, DateTime, String, ForeignKey, Date, Text, Integer, Index, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel
from models.attendance import Attendance
from models.course import Course
from models.enrollment import CourseEnrollment
from models.evaluation import EvaluationRecord
from models.exam import ExamRecord
from models.grade import Grade
from models.parent import Parent
from models.teacher import Teacher
from models.department import Classes, Department, Major
from models.user import User


class StudentStatus(str, PyEnum):
    """学生状态"""

    ACTIVE = "active"  # 在读
    GRADUATED = "graduated"  # 已毕业
    SUSPENDED = "suspended"  # 休学
    TRANSFERRED = "transferred"  # 转学
    DROPPED = "dropped"  # 退学
    EXPELLED = "expelled"  # 开除


class Gender(str, PyEnum):
    """性别"""

    MALE = "male"  # 男
    FEMALE = "female"  # 女
    OTHER = "other"  # 其他


class BehaviorType(str, PyEnum):
    """行为类型"""

    MERIT = "merit"  # 表现优秀
    DEMERIT = "demerit"  # 表现不良
    AWARD = "award"  # 获得奖励
    PUNISHMENT = "punishment"  # 受到处分
    ACTIVITY = "activity"  # 参与活动
    VOLUNTEER = "volunteer"  # 志愿服务
    COMPETITION = "competition"  # 参加比赛
    LEADERSHIP = "leadership"  # 担任干部
    OTHER = "other"  # 其他


class BehaviorLevel(str, PyEnum):
    """行为等级"""

    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    NORMAL = "normal"  # 一般
    POOR = "poor"  # 较差
    SERIOUS = "serious"  # 严重


class BehaviorStatus(str, PyEnum):
    """行为记录状态"""

    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已驳回
    CANCELLED = "cancelled"  # 已取消


class Student(AbstractModel):
    """学生信息模型"""

    __tablename__ = "students"

    # 基本信息
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="姓名")
    gender: Mapped[Gender] = mapped_column(nullable=False, comment="性别")
    birth_date: Mapped[date] = mapped_column(Date, nullable=False, comment="出生日期")
    id_card: Mapped[str] = mapped_column(String(18), unique=True, nullable=False, comment="身份证号")
    phone: Mapped[Optional[str]] = mapped_column(String(20), comment="联系电话")
    email: Mapped[Optional[str]] = mapped_column(String(100), comment="电子邮箱")
    address: Mapped[Optional[str]] = mapped_column(String(200), comment="家庭住址")

    # 学籍信息
    student_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, comment="学号")
    admission_date: Mapped[date] = mapped_column(Date, nullable=False, comment="入学日期")
    graduation_date: Mapped[Optional[date]] = mapped_column(Date, comment="毕业日期")
    status: Mapped[StudentStatus] = mapped_column(
        default=StudentStatus.ACTIVE, nullable=False, index=True, comment="学生状态"
    )
    education_level: Mapped[str] = mapped_column(String(20), nullable=False, comment="学历层次")
    study_mode: Mapped[str] = mapped_column(String(20), nullable=False, comment="学习方式")
    enrollment_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="入学方式")

    # 班级关联
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False, index=True, comment="班级ID"
    )

    # 家长关联
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("parents.id", ondelete="SET NULL"), index=True, comment="家长ID"
    )

    # 学业信息
    total_credits: Mapped[float] = mapped_column(Float(precision=2), default=0.0, comment="总学分")
    gpa: Mapped[Optional[float]] = mapped_column(Float(precision=2), comment="平均绩点")
    rank: Mapped[Optional[int]] = mapped_column(Integer, comment="班级排名")
    scholarship_status: Mapped[Optional[str]] = mapped_column(String(20), comment="奖学金状态")
    academic_status: Mapped[Optional[str]] = mapped_column(String(20), comment="学业状态")

    # 其他信息
    nationality: Mapped[Optional[str]] = mapped_column(String(20), comment="民族")
    political_status: Mapped[Optional[str]] = mapped_column(String(20), comment="政治面貌")
    native_place: Mapped[Optional[str]] = mapped_column(String(50), comment="籍贯")
    photo_url: Mapped[Optional[str]] = mapped_column(String(200), comment="照片URL")
    dormitory: Mapped[Optional[str]] = mapped_column(String(50), comment="宿舍号")
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已注册")
    registration_date: Mapped[Optional[datetime]] = mapped_column(comment="注册时间")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    class_: Mapped["Classes"] = relationship("Classes", back_populates="students", lazy="joined")
    parent: Mapped[Optional["Parent"]] = relationship("Parent", back_populates="students", lazy="joined")
    grades: Mapped[List["Grade"]] = relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )
    behaviors: Mapped[List["Behavior"]] = relationship(
        "Behavior", back_populates="student", cascade="all, delete-orphan"
    )
    enrollments: Mapped[List["CourseEnrollment"]] = relationship(
        "CourseEnrollment", back_populates="student", cascade="all, delete-orphan"
    )
    evaluations: Mapped[List["EvaluationRecord"]] = relationship(
        "EvaluationRecord", back_populates="student", cascade="all, delete-orphan"
    )
    exam_records: Mapped[List["ExamRecord"]] = relationship(
        "ExamRecord", back_populates="student", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("ix_students_name_class", "name", "class_id"),
        Index("ix_students_status_class", "status", "class_id"),
        Index("ix_students_student_id", "student_id"),
        Index("ix_students_gpa_rank", "gpa", "rank"),
    )

    def __repr__(self) -> str:
        return f"<Student {self.student_id} {self.name}>"


class Behavior(AbstractModel):
    """学生行为记录模型"""

    __tablename__ = "student_behaviors"

    # 基本信息
    type: Mapped[BehaviorType] = mapped_column(nullable=False, index=True, comment="行为类型")
    level: Mapped[BehaviorLevel] = mapped_column(
        default=BehaviorLevel.NORMAL, nullable=False, index=True, comment="行为等级"
    )
    status: Mapped[BehaviorStatus] = mapped_column(
        default=BehaviorStatus.DRAFT, nullable=False, index=True, comment="记录状态"
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="行为标题")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="行为描述")
    score: Mapped[int] = mapped_column(Integer, default=0, comment="行为分数")
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="发生日期")
    location: Mapped[Optional[str]] = mapped_column(String(100), comment="发生地点")
    evidence_url: Mapped[Optional[str]] = mapped_column(String(200), comment="证据URL")

    # 处理信息
    process_time: Mapped[Optional[datetime]] = mapped_column(comment="处理时间")
    process_result: Mapped[Optional[str]] = mapped_column(Text, comment="处理结果")
    process_comments: Mapped[Optional[str]] = mapped_column(Text, comment="处理意见")

    # 外键关联
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True, comment="学生ID"
    )
    recorder_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, index=True, comment="记录人ID"
    )
    approver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teachers.id", ondelete="SET NULL"), comment="审批人ID")

    # 关联关系
    student: Mapped["Student"] = relationship("Student", back_populates="behaviors", lazy="joined")
    recorder: Mapped["Teacher"] = relationship("Teacher", foreign_keys=[recorder_id], lazy="joined")
    approver: Mapped[Optional["Teacher"]] = relationship("Teacher", foreign_keys=[approver_id], lazy="joined")

    # 索引
    __table_args__ = (
        Index("ix_student_behaviors_type_level", "type", "level"),
        Index("ix_student_behaviors_status_student", "status", "student_id"),
        Index("ix_student_behaviors_date_student", "date", "student_id"),
    )

    def __repr__(self) -> str:
        return f"<Behavior {self.student.name} {self.type} {self.level}>"


class StudentStatusRecord(AbstractModel):
    """学生学籍变动记录模型"""

    __tablename__ = "student_status_records"

    # 基本信息
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True, comment="学生ID"
    )
    change_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="变动类型：enrollment=入学,transfer=转专业,suspension=休学,resumption=复学,graduation=毕业,dropout=退学",
    )
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, comment="生效日期")
    reason: Mapped[Optional[str]] = mapped_column(Text, comment="变动原因")

    # 院系专业信息
    original_department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), comment="原院系ID"
    )
    original_major_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("majors.id", ondelete="SET NULL"), comment="原专业ID"
    )
    original_class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("classes.id", ondelete="SET NULL"), comment="原班级ID"
    )
    target_department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), comment="目标院系ID"
    )
    target_major_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("majors.id", ondelete="SET NULL"), comment="目标专业ID"
    )
    target_class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("classes.id", ondelete="SET NULL"), comment="目标班级ID"
    )

    # 审核信息
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="状态：pending=待审核,approved=已审核,rejected=已驳回"
    )
    approver_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), comment="审核人ID")
    approve_time: Mapped[Optional[datetime]] = mapped_column(comment="审核时间")
    approve_comments: Mapped[Optional[str]] = mapped_column(Text, comment="审核意见")

    # 关联关系
    student: Mapped["Student"] = relationship("Student", lazy="joined")
    original_department: Mapped[Optional["Department"]] = relationship(
        "Department", foreign_keys=[original_department_id], lazy="joined"
    )
    original_major: Mapped[Optional["Major"]] = relationship("Major", foreign_keys=[original_major_id], lazy="joined")
    original_class: Mapped[Optional["Classes"]] = relationship(
        "Classes", foreign_keys=[original_class_id], lazy="joined"
    )
    target_department: Mapped[Optional["Department"]] = relationship(
        "Department", foreign_keys=[target_department_id], lazy="joined"
    )
    target_major: Mapped[Optional["Major"]] = relationship("Major", foreign_keys=[target_major_id], lazy="joined")
    target_class: Mapped[Optional["Classes"]] = relationship("Classes", foreign_keys=[target_class_id], lazy="joined")
    approver: Mapped[Optional["User"]] = relationship("User", lazy="joined")

    # 索引
    __table_args__ = (
        Index("ix_student_status_records_student", "student_id", "change_type"),
        Index("ix_student_status_records_date", "effective_date", "status"),
    )

    def __repr__(self) -> str:
        return f"<StudentStatusRecord {self.student.name} {self.change_type}>"


class StudentGrade(AbstractModel):
    """学生成绩模型"""

    __tablename__ = "student_grades"

    # 基本信息
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True, comment="学生ID"
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID"
    )
    semester: Mapped[str] = mapped_column(String(20), nullable=False, comment="学期")

    # 成绩信息
    score: Mapped[float] = mapped_column(Float(precision=2), nullable=False, comment="成绩")
    gpa: Mapped[float] = mapped_column(Float(precision=2), nullable=False, comment="绩点")
    credit: Mapped[float] = mapped_column(Float(precision=2), nullable=False, comment="学分")
    grade_point: Mapped[float] = mapped_column(Float(precision=2), nullable=False, comment="等级分")

    # 关联关系
    student: Mapped["Student"] = relationship("Student", lazy="joined")
    course: Mapped["Course"] = relationship("Course", lazy="joined")

    # 索引
    __table_args__ = (
        Index("ix_student_grades_student_course", "student_id", "course_id", "semester"),
        Index("ix_student_grades_semester_student", "semester", "student_id"),
    )

    def __repr__(self) -> str:
        return f"<StudentGrade {self.student.name} {self.course.name} {self.score}>"


class StudentCourse(AbstractModel):
    """学生课程模型"""

    __tablename__ = "student_courses"

    # 基本信息
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True, comment="学生ID"
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True, comment="课程ID"
    )
    semester: Mapped[str] = mapped_column(String(20), nullable=False, comment="学期")
    status: Mapped[str] = mapped_column(String(20), nullable=False, comment="状态")

    # 关联关系
    student: Mapped["Student"] = relationship("Student", lazy="joined")
    course: Mapped["Course"] = relationship("Course", lazy="joined")

    # 索引
    __table_args__ = (
        Index("ix_student_courses_student_course", "student_id", "course_id", "semester"),
        Index("ix_student_courses_semester_student", "semester", "student_id"),
    )

    def __repr__(self) -> str:
        return f"<StudentCourse {self.student.name} {self.course.name} {self.semester}>"
