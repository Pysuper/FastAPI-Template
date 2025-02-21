# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：__init__.py
@Author  ：PySuper
@Date    ：2024-12-19 23:15
@Desc    ：Speedy __init__
"""
from models.audit_log import AuditLogRecord
from models.menu import Menu
from models.enrollment import (
    EnrollmentStatus,
    EnrollmentPeriodType,
    EnrollmentPeriodStatus,
    CourseEnrollment,
    EnrollmentRule,
    EnrollmentPeriod,
)
from models.evaluation import (
    IndicatorType,
    EvaluationStatus,
    EvaluationTargetType,
    EvaluationIndicator,
    EvaluationRule,
    EvaluationRecord,
)
from models.exam import (
    QuestionType,
    ExamStatus,
    ExamRecordStatus,
    Exam,
    Question,
    ExamRecord,
    StudentAnswer,
)
from models.notification import (
    NotificationType,
    FeedbackStatus,
    ParentFeedback,
    FeedbackReply,
    Notification,
    NotificationRecord,
)
from models.parent import Parent, ParentType
from models.permission import Permission
from models.student import (
    Student,
    StudentStatus,
    Gender,
    BehaviorType,
    BehaviorLevel,
    BehaviorStatus,
    Behavior,
    StudentStatusRecord,
    StudentGrade,
    StudentCourse,
)
from models.teacher import Teacher
from models.user import User
from models.role import Role, users_roles, role_permissions
from models.system import SystemLog
from models.department import Department, Major, Classes

__all__ = [
    # Parent models
    "Parent",
    "ParentType",
    # Department models
    "Department",
    "Major",
    "Classes",
    # Teacher models
    "Teacher",
    # Student models
    "Student",
    "StudentStatus",
    "Gender",
    "BehaviorType",
    "BehaviorLevel",
    "BehaviorStatus",
    "Behavior",
    "StudentStatusRecord",
    "StudentGrade",
    "StudentCourse",
    # Notification models
    "NotificationType",
    "FeedbackStatus",
    "ParentFeedback",
    "FeedbackReply",
    "Notification",
    "NotificationRecord",
    # Evaluation models
    "IndicatorType",
    "EvaluationStatus",
    "EvaluationTargetType",
    "EvaluationIndicator",
    "EvaluationRule",
    "EvaluationRecord",
    # Enrollment models
    "EnrollmentStatus",
    "EnrollmentPeriodType",
    "EnrollmentPeriodStatus",
    "CourseEnrollment",
    "EnrollmentRule",
    "EnrollmentPeriod",
    # Exam models
    "QuestionType",
    "ExamStatus",
    "ExamRecordStatus",
    "Exam",
    "Question",
    "ExamRecord",
    "StudentAnswer",
    # RBAC
    "User",
    "Permission",
    "Role",
    "users_roles",
    "role_permissions",
    # System
    "SystemLog",
    "Menu",
    "AuditLogRecord",
]
