# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：__init__.py
@Author  ：PySuper
@Date    ：2024/12/30 17:40 
@Desc    ：Speedy schemas __init__.py
"""

from schemas.activity import *
from schemas.class_ import *
from schemas.config import *
from schemas.course import *
from schemas.department import *
from schemas.enrollment import *
from schemas.evaluation import *
from schemas.exam import *
from schemas.grade import *
from schemas.major import *
from schemas.manager import *
from schemas.menus import *
from schemas.message import *
from schemas.notification import *
from schemas.permission import *
from schemas.record import *
from schemas.resource import *
from schemas.roles import *
from schemas.school import *
from schemas.student import *
from schemas.system import *
from schemas.tasks import *
from schemas.teacher import *
from schemas.teaching import *
from schemas.title import *
from schemas.user import *
from schemas.validator import *

__all__ = [
    # Activity
    "ActivityBase",
    "ActivityCreate",
    "ActivityUpdate",
    # Class
    "ClassBase",
    "ClassCreate",
    "ClassUpdate",
    # Config
    "ConfigCreate",
    "ConfigUpdate",
    # Course
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    # Department
    "DepartmentCreate",
    "DepartmentUpdate",
    # Enrollment
    # Evaluation
    # Exam
    "ExamBase",
    "ExamCreate",
    "ExamUpdate",
    # Grade
    "GradeBase",
    "GradeCreate",
    "GradeUpdate",
    # Major
    "MajorBase",
    "MajorCreate",
    "MajorUpdate",
    # Manager
    # Menu
    "MenuCreate",
    "MenuUpdate",
    # Message
    "MessageCreate",
    "MessageUpdate",
    # Notification
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationFilter",
    # Permission
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    # Record
    "RecordCreate",
    "RecordUpdate",
    "RecordResponse",
    # Resource
    "ResourceBase",
    "ResourceCreate",
    "ResourceUpdate",
    # Role
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    # School
    # Student
    "StudentBase",
    "StudentCreate",
    "StudentUpdate",
    # System
    # Task
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    # Teacher
    "TeacherBase",
    "TeacherCreate",
    "TeacherUpdate",
    # Teaching
    # Title
    "TitleCreate",
    "TitleUpdate",
    "TeacherBase",
    "TeacherCreate",
    "TeacherUpdate",
    "TeacherFilter",
    "TeacherResponse",
    "TitleCreate",
    "TitleUpdate",
    "TitleResponse",
    "AttendanceCreate",
    "AttendanceUpdate",
    "AttendanceResponse",
    # User
    "UserCreate",
    "UserUpdate",
    # Validator
]
