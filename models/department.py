from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import String, ForeignKey, Integer, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class DepartmentStatus(str, PyEnum):
    """部门状态"""

    ACTIVE = "active"  # 正常
    DISABLED = "disabled"  # 禁用
    MERGED = "merged"  # 已合并
    SPLIT = "split"  # 已拆分
    ARCHIVED = "archived"  # 已归档


class MajorStatus(str, PyEnum):
    """专业状态"""

    ACTIVE = "active"  # 正常
    DISABLED = "disabled"  # 停招
    MERGED = "merged"  # 已合并
    SPLIT = "split"  # 已拆分
    ARCHIVED = "archived"  # 已归档


class ClassStatus(str, PyEnum):
    """班级状态"""

    ACTIVE = "active"  # 正常
    GRADUATED = "graduated"  # 已毕业
    MERGED = "merged"  # 已合并
    SPLIT = "split"  # 已拆分
    ARCHIVED = "archived"  # 已归档


class Department(AbstractModel):
    """院系模型"""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="ID")

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="院系名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="院系编码")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="院系描述")

    # 层级关系
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        index=True,
        comment="父级院系ID",
    )
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    level: Mapped[int] = mapped_column(Integer, default=1, comment="层级")

    # 状态信息
    status: Mapped[DepartmentStatus] = mapped_column(
        default=DepartmentStatus.ACTIVE,
        nullable=False,
        index=True,
        comment="状态",
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否系统院系")

    # 其他信息
    leader: Mapped[Optional[str]] = mapped_column(String(50), comment="负责人")
    phone: Mapped[Optional[str]] = mapped_column(String(20), comment="联系电话")
    email: Mapped[Optional[str]] = mapped_column(String(100), comment="电子邮箱")
    address: Mapped[Optional[str]] = mapped_column(String(200), comment="地址")
    website: Mapped[Optional[str]] = mapped_column(String(200), comment="网站")
    founded_date: Mapped[Optional[datetime]] = mapped_column(comment="成立日期")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    parent: Mapped[Optional["Department"]] = relationship(
        "Department",
        remote_side=[id],
        back_populates="children",
        lazy="joined",
    )
    children: Mapped[List["Department"]] = relationship(
        "Department",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    majors: Mapped[List["Major"]] = relationship("Major", back_populates="department", cascade="all, delete-orphan")
    teachers: Mapped[List["Teacher"]] = relationship(
        "Teacher",
        back_populates="department",
        cascade="all, delete-orphan",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="department",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index(
            "ix_departments_parent_sort",
            "parent_id",
            "sort",
        ),
        Index(
            "ix_departments_status_level",
            "status",
            "level",
        ),
    )

    def __repr__(self) -> str:
        return f"<Department {self.code} {self.name}>"


class Major(AbstractModel):
    """专业模型"""

    __tablename__ = "majors"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="专业名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="专业编码")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="专业描述")
    duration: Mapped[int] = mapped_column(Integer, default=4, comment="学制年限")

    # 状态信息
    status: Mapped[MajorStatus] = mapped_column(default=MajorStatus.ACTIVE, nullable=False, index=True, comment="状态")

    # 其他信息
    leader: Mapped[Optional[str]] = mapped_column(String(50), comment="负责人")
    introduction: Mapped[Optional[str]] = mapped_column(Text, comment="专业介绍")
    requirements: Mapped[Optional[str]] = mapped_column(Text, comment="培养要求")
    career_prospects: Mapped[Optional[str]] = mapped_column(Text, comment="就业方向")
    founded_date: Mapped[Optional[datetime]] = mapped_column(comment="成立日期")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="院系ID",
    )

    # 关联关系
    department: Mapped["Department"] = relationship("Department", back_populates="majors", lazy="joined")
    classes: Mapped[List["Classes"]] = relationship("Classes", back_populates="major", cascade="all, delete-orphan")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="major", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index(
            "ix_majors_department_status",
            "department_id",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Major {self.code} {self.name}>"


class Classes(AbstractModel):
    """班级模型"""

    __tablename__ = "classes"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="班级名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="班级编码")
    grade: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="年级")
    capacity: Mapped[int] = mapped_column(Integer, default=50, comment="班级容量")

    # 状态信息
    status: Mapped[ClassStatus] = mapped_column(default=ClassStatus.ACTIVE, nullable=False, index=True, comment="状态")

    # 其他信息
    monitor: Mapped[Optional[str]] = mapped_column(String(50), comment="班长")
    vice_monitor: Mapped[Optional[str]] = mapped_column(String(50), comment="副班长")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="班级描述")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 外键关联
    major_id: Mapped[int] = mapped_column(
        ForeignKey("majors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="专业ID",
    )
    teacher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"),
        index=True,
        comment="班主任ID",
    )

    # 关联关系
    major: Mapped["Major"] = relationship("Major", back_populates="classes", lazy="joined")
    teacher: Mapped[Optional["Teacher"]] = relationship("Teacher", back_populates="managed_classes", lazy="joined")
    students: Mapped[List["Student"]] = relationship("Student", back_populates="class_", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index(
            "ix_classes_major_grade",
            "major_id",
            "grade",
        ),
        Index(
            "ix_classes_status_teacher",
            "status",
            "teacher_id",
        ),
    )

    def __repr__(self) -> str:
        return f"<Classes {self.code} {self.name}>"
