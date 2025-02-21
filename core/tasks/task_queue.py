"""
任务队列管理器
实现异步任务的调度和执行
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from core.strong.event_bus import Event, event_bus

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


@dataclass
class TaskResult:
    """任务执行结果"""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration(self) -> Optional[float]:
        """获取任务执行时长"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class Task:
    """异步任务"""

    def __init__(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        retry_times: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        schedule_time: Optional[Union[datetime, float]] = None,
    ):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.schedule_time = schedule_time
        self.status = TaskStatus.SCHEDULED if schedule_time else TaskStatus.PENDING
        self.result: Optional[TaskResult] = None
        self._current_retry = 0
        self._future: Optional[asyncio.Future] = None

    async def execute(self) -> TaskResult:
        """执行任务"""
        if self.status == TaskStatus.CANCELLED:
            return self._create_result(TaskStatus.CANCELLED)

        self.status = TaskStatus.RUNNING
        start_time = time.time()

        try:
            if self.timeout:
                result = await asyncio.wait_for(
                    self._execute_with_retry(),
                    timeout=self.timeout,
                )
            else:
                result = await self._execute_with_retry()

            self.status = TaskStatus.COMPLETED
            return self._create_result(
                TaskStatus.COMPLETED,
                result=result,
                start_time=start_time,
                end_time=time.time(),
            )

        except asyncio.TimeoutError as e:
            self.status = TaskStatus.FAILED
            return self._create_result(
                TaskStatus.FAILED,
                error=e,
                start_time=start_time,
                end_time=time.time(),
            )
        except Exception as e:
            self.status = TaskStatus.FAILED
            return self._create_result(
                TaskStatus.FAILED,
                error=e,
                start_time=start_time,
                end_time=time.time(),
            )

    async def _execute_with_retry(self) -> Any:
        """执行任务(带重试)"""
        while True:
            try:
                if asyncio.iscoroutinefunction(self.func):
                    return await self.func(*self.args, **self.kwargs)
                return self.func(*self.args, **self.kwargs)
            except Exception as e:
                self._current_retry += 1
                if self._current_retry > self.retry_times:
                    raise

                logger.warning(
                    f"Task {self.task_id} failed, retrying {self._current_retry}/{self.retry_times}: {str(e)}"
                )
                await asyncio.sleep(self.retry_delay)

    def _create_result(
        self,
        status: TaskStatus,
        result: Any = None,
        error: Optional[Exception] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> TaskResult:
        """创建任务结果"""
        self.result = TaskResult(
            task_id=self.task_id,
            status=status,
            result=result,
            error=error,
            start_time=start_time,
            end_time=end_time,
        )
        return self.result

    def cancel(self) -> None:
        """取消任务"""
        if self.status in (TaskStatus.PENDING, TaskStatus.SCHEDULED):
            self.status = TaskStatus.CANCELLED
            if self._future and not self._future.done():
                self._future.cancel()


class TaskQueue:
    """任务队列管理器"""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self._tasks: Dict[str, Task] = {}
        self._queue: asyncio.Queue[Task] = asyncio.Queue()
        self._workers: List[asyncio.Task] = []
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """启动任务队列"""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler())

        for _ in range(self.max_workers):
            worker = asyncio.create_task(self._worker())
            self._workers.append(worker)

    async def stop(self) -> None:
        """停止任务队列"""
        if not self._running:
            return

        self._running = False

        # 取消调度器
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        # 取消所有任务
        for task in self._tasks.values():
            task.cancel()

        # 等待队列清空
        await self._queue.join()

        # 取消所有工作者
        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def submit(self, func: Callable, *args, task_id: Optional[str] = None, **kwargs) -> Task:
        """
        提交任务
        :param func: 任务函数
        :param args: 位置参数
        :param task_id: 任务ID
        :param kwargs: 关键字参数
        :return: 任务对象
        """
        if not self._running:
            raise RuntimeError("Task queue is not running")

        task_id = task_id or str(id(func))
        task = Task(task_id, func, args, kwargs)
        self._tasks[task_id] = task
        await self._queue.put(task)

        # 发布任务提交事件
        await event_bus.publish(Event("task_submitted", task))

        return task

    async def schedule(
        self,
        func: Callable,
        schedule_time: Union[datetime, float],
        *args,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> Task:
        """
        调度任务
        :param func: 任务函数
        :param schedule_time: 调度时间
        :param args: 位置参数
        :param task_id: 任务ID
        :param kwargs: 关键字参数
        :return: 任务对象
        """
        if not self._running:
            raise RuntimeError("Task queue is not running")

        task_id = task_id or str(id(func))
        task = Task(task_id, func, args, kwargs, schedule_time=schedule_time)
        self._tasks[task_id] = task

        # 发布任务调度事件
        await event_bus.publish(Event("task_scheduled", task))

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.get_task(task_id)
        if task:
            task.cancel()
            # 发布任务取消事件
            await event_bus.publish(Event("task_cancelled", task))
            return True
        return False

    async def _worker(self) -> None:
        """工作者协程"""
        while self._running:
            try:
                task = await self._queue.get()
                if task.status != TaskStatus.CANCELLED:
                    result = await task.execute()
                    # 发布任务完成事件
                    await event_bus.publish(
                        Event(
                            "task_completed" if result.status == TaskStatus.COMPLETED else "task_failed",
                            task,
                        )
                    )
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")

    async def _scheduler(self) -> None:
        """调度器协程"""
        while self._running:
            try:
                now = time.time()
                for task in list(self._tasks.values()):
                    if (
                        task.status == TaskStatus.SCHEDULED
                        and isinstance(task.schedule_time, (int, float))
                        and task.schedule_time <= now
                    ):
                        task.status = TaskStatus.PENDING
                        await self._queue.put(task)

                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

    async def init(self):
        pass


# 创建默认任务队列实例
task_queue = TaskQueue()

# 导出
__all__ = [
    "task_queue",
    "TaskQueue",
    "Task",
    "TaskStatus",
    "TaskResult",
]
