# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：task.py
@Author  ：PySuper
@Date    ：2025-01-04 18:11
@Desc    ：任务系统相关异常类定义
"""
from typing import Any, Dict, Optional


class TasksException(Exception):
    """
    任务系统基础异常类

    用于表示所有任务相关异常的基类。继承自Python内置的Exception类。

    Attributes:
        message: 错误消息
        details: 详细错误信息
        context: 异常上下文信息
    """

    def __init__(self, message: str, details: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details
        self.context = context or {}
        super().__init__(self.message)


class TaskConfigException(TasksException):
    """
    任务配置异常

    当任务配置出现问题时抛出，如配置参数无效、缺失必要配置等。
    """

    def __init__(
        self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None, **kwargs
    ) -> None:
        context = {"config_key": config_key, "config_value": config_value, **kwargs}
        super().__init__(message, context=context)


class TaskExecutionException(TasksException):
    """
    任务执行异常

    当任务执行过程中出现错误时抛出，如运行时错误、超时等。
    """

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        execution_time: Optional[float] = None,
        **kwargs,
    ) -> None:
        context = {"task_id": task_id, "task_name": task_name, "execution_time": execution_time, **kwargs}
        super().__init__(message, context=context)


class TaskInitException(TasksException):
    """
    任务初始化异常

    当任务系统初始化失败时抛出，如Celery应用创建失败、Worker启动失败等。
    """

    def __init__(
        self, message: str, component: Optional[str] = None, init_params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> None:
        context = {"component": component, "init_params": init_params, **kwargs}
        super().__init__(message, context=context)


class TaskNotFoundException(TasksException):
    """
    任务未找到异常

    当尝试访问或操作不存在的任务时抛出。
    """

    def __init__(self, message: str, task_id: Optional[str] = None, task_name: Optional[str] = None, **kwargs) -> None:
        context = {"task_id": task_id, "task_name": task_name, **kwargs}
        super().__init__(message, context=context)


class TaskQueueException(TasksException):
    """
    任务队列异常

    当任务队列操作失败时抛出，如队列满、消息代理连接失败等。
    """

    def __init__(
        self,
        message: str,
        queue_name: Optional[str] = None,
        operation: Optional[str] = None,
        queue_size: Optional[int] = None,
        **kwargs,
    ) -> None:
        context = {"queue_name": queue_name, "operation": operation, "queue_size": queue_size, **kwargs}
        super().__init__(message, context=context)


class TaskTimeoutException(TasksException):
    """
    任务超时异常

    当任务执行超过预定时间限制时抛出。
    """

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        actual_runtime: Optional[float] = None,
        **kwargs,
    ) -> None:
        context = {"task_id": task_id, "timeout_seconds": timeout_seconds, "actual_runtime": actual_runtime, **kwargs}
        super().__init__(message, context=context)


class TaskCancelledException(TasksException):
    """
    任务取消异常

    当任务被手动取消或因系统原因被取消时抛出。
    """

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        cancel_reason: Optional[str] = None,
        cancelled_by: Optional[str] = None,
        **kwargs,
    ) -> None:
        context = {"task_id": task_id, "cancel_reason": cancel_reason, "cancelled_by": cancelled_by, **kwargs}
        super().__init__(message, context=context)


class TaskRetryException(TasksException):
    """
    任务重试异常

    当任务需要重试时抛出，通常包含重试次数和间隔信息。
    """

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        retry_count: Optional[int] = None,
        retry_delay: Optional[float] = None,
        max_retries: Optional[int] = None,
        **kwargs,
    ) -> None:
        context = {
            "task_id": task_id,
            "retry_count": retry_count,
            "retry_delay": retry_delay,
            "max_retries": max_retries,
            **kwargs,
        }
        super().__init__(message, context=context)


class TaskDependencyException(TasksException):
    """
    任务依赖异常

    当任务的依赖任务执行失败或不满足条件时抛出。
    """

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        dependency_task_id: Optional[str] = None,
        dependency_status: Optional[str] = None,
        **kwargs,
    ) -> None:
        context = {
            "task_id": task_id,
            "dependency_task_id": dependency_task_id,
            "dependency_status": dependency_status,
            **kwargs,
        }
        super().__init__(message, context=context)
