# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2024/12/30 10:34 
@Desc    ：任务管理器模块

提供统一的任务管理功能，包含以下特性：
    1. 任务配置管理
    2. 任务队列管理
    3. 任务调度管理
    4. 任务执行管理
    5. 任务监控管理
    6. 任务日志管理
    7. 任务重试管理
    8. 任务超时管理

使用示例：
    ```python
    # 初始化
    await task_manager.init()

    # 添加任务
    task_id = await task_manager.add_task(
        name="task1",
        func=my_task_func,
        args=(1, 2),
        kwargs={"x": 1}
    )

    # 获取任务状态
    status = await task_manager.get_task_status(task_id)

    # 取消任务
    await task_manager.cancel_task(task_id)

    # 关闭
    await task_manager.close()
    ```
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from celery import Celery
from celery.apps.worker import Worker
from celery.result import AsyncResult

from core.config.setting import settings
from core.exceptions.system.task import (
    TaskConfigException,
    TaskExecutionException,
    TaskInitException,
    TaskNotFoundException,
    TaskQueueException,
)
from core.tasks.config import TaskConfig

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器"""

    def __init__(self, config: Optional[TaskConfig] = None):
        """
        初始化任务管理器

        Args:
            config: 任务配置对象
        """
        self.config = config or TaskConfig()
        self.app: Optional[Celery] = None
        self.workers: List[Worker] = []
        self._initialized = False

    async def init(self) -> None:
        """
        初始化任务管理器
        """
        if self._initialized:
            return

        try:
            # 创建Celery应用
            self.app = Celery(
                "project_name",
                broker=settings.task.broker_url,
                backend=settings.task.result_backend,
            )

            # 配置Celery
            self.app.conf.update(
                task_serializer="json",
                accept_content=["json"],
                result_serializer="json",
                timezone="Asia/Shanghai",
                enable_utc=True,
                worker_prefetch_multiplier=1,
                worker_max_tasks_per_child=1000,
                worker_max_memory_per_child=50000,  # 50MB
                task_time_limit=self.config.task_timeout,
                broker_connection_retry=True,
                broker_connection_max_retries=self.config.max_retries,
                broker_connection_retry_on_startup=True,
                redis_max_connections=self.config.redis_config.max_connections,
                broker_transport_options={
                    "socket_timeout": self.config.redis_config.socket_timeout,
                    "socket_connect_timeout": self.config.redis_config.socket_connect_timeout,
                },
            )

            # 自动发现任务
            self.app.autodiscover_tasks(["core.tasks.jobs"])

            # 初始化工作进程
            await self._start_workers()

            self._initialized = True
            logger.info("任务管理器初始化成功")

        except Exception as e:
            logger.error(f"任务管理器初始化失败: {e}")
            raise TaskInitException(f"任务管理器初始化失败: {str(e)}")

    async def _start_workers(self) -> None:
        """
        启动工作进程
        """
        try:
            for _ in range(self.config.num_workers):
                worker = Worker(
                    app=self.app,
                    hostname=None,  # 自动生成主机名
                    queues=["celery"],  # 默认队列
                    concurrency=1,  # 每个worker一个进程
                    loglevel="INFO",
                    without_heartbeat=True,  # 禁用心跳
                    without_mingle=True,  # 禁用mingle
                    without_gossip=True,  # 禁用gossip
                    pool="solo",  # 使用单进程模式
                    task_events=False,  # 禁用任务事件
                )
                self.workers.append(worker)
                # 使用异步方式启动worker
                await asyncio.to_thread(worker.start)

            logger.info(f"成功启动 {len(self.workers)} 个工作进程")

        except Exception as e:
            logger.error(f"启动工作进程失败: {e}")
            raise TaskInitException(f"启动工作进程失败: {str(e)}")

    async def stop(self) -> None:
        """
        停止任务管理器
        """
        if not self._initialized:
            return

        try:
            # 停止所有工作进程
            for worker in self.workers:
                worker.stop()
            self.workers.clear()

            # 关闭Celery应用
            if self.app:
                self.app.close()
                self.app = None

            self._initialized = False
            logger.info("任务管理器已停止")

        except Exception as e:
            logger.error(f"停止任务管理器失败: {e}")
            raise TaskExecutionException(f"停止任务管理器失败: {str(e)}")

    async def submit_task(
        self,
        task_name: str,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        countdown: Optional[int] = None,
    ) -> str:
        """
        提交任务

        Args:
            task_name: 任务名称
            args: 位置参数
            kwargs: 关键字参数
            countdown: 延迟执行时间(秒)

        Returns:
            任务ID

        Raises:
            TaskNotFoundException: 任务不存在
            TaskQueueException: 任务提交失败
        """
        if not self._initialized:
            raise TaskInitException("任务管理器未初始化")

        try:
            task = self.app.tasks.get(task_name)
            if not task:
                raise TaskNotFoundException(f"任务 {task_name} 不存在")

            result = task.apply_async(
                args=args or (),
                kwargs=kwargs or {},
                countdown=countdown,
            )
            return result.id

        except Exception as e:
            logger.error(f"提交任务失败: {e}")
            raise TaskQueueException(f"提交任务失败: {str(e)}")

    async def get_task_result(self, task_id: str) -> Any:
        """
        获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            任务结果

        Raises:
            TaskNotFoundException: 任务不存在
            TaskExecutionException: 任务执行失败
        """
        if not self._initialized:
            raise TaskInitException("任务管理器未初始化")

        try:
            result = AsyncResult(task_id, app=self.app)
            if not result:
                raise TaskNotFoundException(f"任务 {task_id} 不存在")

            if result.failed():
                raise TaskExecutionException(f"任务执行失败: {result.result}")

            return result.result

        except Exception as e:
            logger.error(f"获取任务结果失败: {e}")
            raise TaskExecutionException(f"获取任务结果失败: {str(e)}")

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息

        Raises:
            TaskNotFoundException: 任务不存在
        """
        if not self._initialized:
            raise TaskInitException("任务管理器未初始化")

        try:
            result = AsyncResult(task_id, app=self.app)
            if not result:
                raise TaskNotFoundException(f"任务 {task_id} 不存在")

            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None,
            }

        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            raise TaskExecutionException(f"获取任务状态失败: {str(e)}")

    async def revoke_task(self, task_id: str, terminate: bool = False) -> None:
        """
        撤销任务

        Args:
            task_id: 任务ID
            terminate: 是否终止正在执行的任务

        Raises:
            TaskNotFoundException: 任务不存在
            TaskExecutionException: 任务撤销失败
        """
        if not self._initialized:
            raise TaskInitException("任务管理器未初始化")

        try:
            result = AsyncResult(task_id, app=self.app)
            if not result:
                raise TaskNotFoundException(f"任务 {task_id} 不存在")

            result.revoke(terminate=terminate)
            logger.info(f"任务 {task_id} 已撤销")

        except Exception as e:
            logger.error(f"撤销任务失败: {e}")
            raise TaskExecutionException(f"撤销任务失败: {str(e)}")


# 全局任务管理器实例
task_manager = TaskManager()

# 导出
__all__ = [
    "TaskConfig",
    "TaskManager",
    "task_manager",
]
