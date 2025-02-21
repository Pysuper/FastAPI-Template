"""
学术/教务相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class AcademicBusinessException(BusinessException):
    """学术/教务业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.BUSINESS_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化学术/教务业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"academic_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class CourseNotFoundException(AcademicBusinessException):
    """课程不存在异常"""

    def __init__(
        self,
        message: str = "课程不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"course_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class StudentNotFoundException(AcademicBusinessException):
    """学生不存在异常"""

    def __init__(
        self,
        message: str = "学生不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"student_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TeacherNotFoundException(AcademicBusinessException):
    """教师不存在异常"""

    def __init__(
        self,
        message: str = "教师不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"teacher_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class GradeException(AcademicBusinessException):
    """成绩异常"""

    def __init__(
        self,
        message: str = "成绩错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"grade_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class AttendanceException(AcademicBusinessException):
    """考勤异常"""

    def __init__(
        self,
        message: str = "考勤错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"attendance_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class EnrollmentException(AcademicBusinessException):
    """选课异常"""

    def __init__(
        self,
        message: str = "选课错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"enrollment_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class ScheduleConflictException(AcademicBusinessException):
    """课程时间冲突异常"""

    def __init__(
        self,
        message: str = "课程时间冲突",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"schedule_conflict": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
