# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：users.py
@Author  ：PySuper
@Date    ：2024/12/30 16:32 
@Desc    ：Speedy users.py
"""
from enum import Enum


class TokenType(str, Enum):
    ACCESS = "access"  # 访问令牌
    REFRESH = "refresh"  # 刷新令牌
    RESET_PASSWORD = "reset_password"  # 重置密码令牌


class Gender(str, Enum):
    """性别枚举"""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class StudentStatus(str, Enum):
    """学生状态枚举"""

    ACTIVE = "active"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"
    DROPPED = "dropped"


class CourseStatus(str, Enum):
    """课程状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class GradeStatus(str, Enum):
    """成绩状态枚举"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class GradeLevel(str, Enum):
    """成绩等级枚举"""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class SelectionStatus(str, Enum):
    """选课状态枚举"""

    SELECTED = "selected"
    DROPPED = "dropped"
    COMPLETED = "completed"
