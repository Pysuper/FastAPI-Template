# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：base.py
@Author  ：PySuper
@Date    ：2024/12/30 10:34 
@Desc    ：任务基础类模块

提供任务处理的基础类，包含以下特性：
    1. 数据库会话管理
    2. 任务生命周期钩子
    3. 错误处理
    4. 日志记录
    5. 重试机制
    6. 成功/失败处理
"""

from logging import Logger
from typing import Any, Dict, Optional, Tuple

from celery import Task
from sqlalchemy.orm import Session

from db.core.session import SessionLocal
from core.loge.logger import CustomLogger


class DatabaseTask(Task):
    """
    带数据库会话的基础任务类

    提供数据库会话的自动管理功能，确保任务执行完成后正确关闭会话
    """

    _db: Optional[Session] = None
    logger: Logger = CustomLogger("task.database")

    @property
    def db(self) -> Session:
        """
        获取数据库会话

        Returns:
            Session: SQLAlchemy会话实例
        """
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args: Any, **kwargs: Any) -> None:
        """
        任务完成后的清理工作

        负责关闭数据库会话，释放资源
        """
        if self._db is not None:
            self._db.close()
            self._db = None
            self.logger.debug("Database session closed")


class BaseTask(DatabaseTask):
    """
    基础任务类

    继承自DatabaseTask，提供通用的任务处理逻辑：
        1. 错误处理和日志记录
        2. 重试机制
        3. 任务状态管理
        4. 结果处理
    """

    abstract = True
    logger: Logger = CustomLogger("task.base")

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        einfo: Any,
    ) -> None:
        """
        任务失败时的处理

        Args:
            exc: 异常对象
            task_id: 任务ID
            args: 位置参数
            kwargs: 关键字参数
            einfo: 错误信息
        """
        # 记录错误日志
        self.logger.error(
            f"Task {task_id} failed: {exc}\n" f"Args: {args}\n" f"Kwargs: {kwargs}",
            exc_info=einfo,
        )

        # 可以在这里添加告警通知等逻辑
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        einfo: Any,
    ) -> None:
        """
        任务重试时的处理

        Args:
            exc: 异常对象
            task_id: 任务ID
            args: 位置参数
            kwargs: 关键字参数
            einfo: 错误信息
        """
        self.logger.warning(
            f"Task {task_id} retrying: {exc}\n" f"Args: {args}\n" f"Kwargs: {kwargs}",
            exc_info=einfo,
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(
        self,
        retval: Any,
        task_id: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        """
        任务成功时的处理

        Args:
            retval: 任务返回值
            task_id: 任务ID
            args: 位置参数
            kwargs: 关键字参数
        """
        self.logger.info(f"Task {task_id} succeeded\n" f"Args: {args}\n" f"Kwargs: {kwargs}\n" f"Result: {retval}")
        super().on_success(retval, task_id, args, kwargs)


# 导出
__all__ = [
    "DatabaseTask",
    "BaseTask",
]
