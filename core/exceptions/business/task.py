"""
任务管理相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class TaskBusinessException(BusinessException):
    """任务管理业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.TASK_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化任务管理业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"task_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class TaskNotFoundException(TaskBusinessException):
    """任务不存在异常"""

    def __init__(
        self,
        message: str = "任务不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"task_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TaskExecutionException(TaskBusinessException):
    """任务执行异常"""

    def __init__(
        self,
        message: str = "任务执行失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"execution_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TaskTimeoutException(TaskBusinessException):
    """任务超时异常"""

    def __init__(
        self,
        message: str = "任务执行超时",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"task_timeout": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TaskScheduleException(TaskBusinessException):
    """任务调度异常"""

    def __init__(
        self,
        message: str = "任务调度失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"schedule_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TaskConcurrencyException(TaskBusinessException):
    """任务并发异常"""

    def __init__(
        self,
        message: str = "任务并发限制",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"concurrency_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class TaskDependencyException(TaskBusinessException):
    """任务依赖异常"""

    def __init__(
        self,
        message: str = "任务依赖错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"dependency_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
