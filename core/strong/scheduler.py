"""
定时任务调度器
实现定时任务和周期性任务的调度
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from croniter import croniter

from core.strong.event_bus import Event, event_bus
from core.strong.locks import lock_manager
from core.strong.metrics import metrics_collector

logger = logging.getLogger(__name__)


class JobStatus:
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """定时任务"""

    def __init__(
        self,
        func: Callable,
        job_id: str,
        trigger: Union[str, datetime, timedelta],
        args: tuple = (),
        kwargs: dict = None,
        max_instances: int = 1,
        misfire_grace_time: int = 60,
        coalesce: bool = True,
    ):
        """
        初始化
        :param func: 任务函数
        :param job_id: 任务ID
        :param trigger: 触发器(cron表达式、datetime或timedelta)
        :param args: 位置参数
        :param kwargs: 关键字参数
        :param max_instances: 最大实例数
        :param misfire_grace_time: 错过触发的宽限时间(秒)
        :param coalesce: 是否合并错过的触发
        """
        self.func = func
        self.job_id = job_id
        self.trigger = trigger
        self.args = args
        self.kwargs = kwargs or {}
        self.max_instances = max_instances
        self.misfire_grace_time = misfire_grace_time
        self.coalesce = coalesce

        self.next_run_time: Optional[datetime] = None
        self.last_run_time: Optional[datetime] = None
        self.running_instances = 0
        self.status = JobStatus.PENDING
        self._lock = asyncio.Lock()

    def get_next_run_time(self, now: Optional[datetime] = None) -> Optional[datetime]:
        """
        获取下次运行时间
        :param now: 当前时间
        :return: 下次运行时间
        """
        if not now:
            now = datetime.now()

        if isinstance(self.trigger, str):
            # Cron表达式
            try:
                cron = croniter(self.trigger, now)
                return cron.get_next(datetime)
            except Exception as e:
                logger.error(f"Invalid cron expression: {self.trigger}", exc_info=e)
                return None
        elif isinstance(self.trigger, datetime):
            # 指定时间
            return self.trigger if self.trigger > now else None
        elif isinstance(self.trigger, timedelta):
            # 时间间隔
            if not self.last_run_time:
                return now + self.trigger
            return self.last_run_time + self.trigger
        return None

    async def run(self) -> None:
        """运行任务"""
        if self.running_instances >= self.max_instances:
            logger.warning(f"Job {self.job_id} has reached max instances: {self.max_instances}")
            return

        async with self._lock:
            self.running_instances += 1
            self.status = JobStatus.RUNNING

        start_time = datetime.now()
        success = False
        error = None

        try:
            if asyncio.iscoroutinefunction(self.func):
                await self.func(*self.args, **self.kwargs)
            else:
                self.func(*self.args, **self.kwargs)
            success = True
            self.status = JobStatus.COMPLETED

        except Exception as e:
            error = e
            self.status = JobStatus.FAILED
            logger.error(f"Job {self.job_id} failed", exc_info=e)

        finally:
            duration = (datetime.now() - start_time).total_seconds()

            # 更新指标
            metrics_collector.observe(
                "scheduler_job_duration_seconds", duration, {"job_id": self.job_id, "success": str(success)}
            )

            if success:
                metrics_collector.increment("scheduler_jobs_completed_total", 1, {"job_id": self.job_id})
            else:
                metrics_collector.increment("scheduler_jobs_failed_total", 1, {"job_id": self.job_id})

            # 发布任务完成事件
            await event_bus.publish(
                Event(
                    "job_completed",
                    {
                        "job_id": self.job_id,
                        "success": success,
                        "error": str(error) if error else None,
                        "duration": duration,
                    },
                )
            )

            async with self._lock:
                self.running_instances -= 1
                self.last_run_time = start_time

            # 计算下次运行时间
            self.next_run_time = self.get_next_run_time()


class Scheduler:
    """任务调度器"""

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """启动调度器"""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")

    async def stop(self) -> None:
        """停止调度器"""
        if not self._running:
            return

        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        logger.info("Scheduler stopped")

    async def add_job(
        self, func: Callable, trigger: Union[str, datetime, timedelta], job_id: Optional[str] = None, **kwargs
    ) -> Job:
        """
        添加任务
        :param func: 任务函数
        :param trigger: 触发器
        :param job_id: 任务ID
        :param kwargs: 任务参数
        :return: 任务对象
        """
        if not job_id:
            job_id = f"{func.__name__}_{id(func)}"

        if job_id in self._jobs:
            raise ValueError(f"Job {job_id} already exists")

        job = Job(func, job_id, trigger, **kwargs)
        job.next_run_time = job.get_next_run_time()

        async with self._lock:
            self._jobs[job_id] = job

        # 发布任务添加事件
        await event_bus.publish(Event("job_added", {"job_id": job_id}))

        return job

    async def remove_job(self, job_id: str) -> None:
        """
        移除任务
        :param job_id: 任务ID
        """
        async with self._lock:
            if job_id in self._jobs:
                job = self._jobs.pop(job_id)
                job.status = JobStatus.CANCELLED

                # 发布任务移除事件
                await event_bus.publish(Event("job_removed", {"job_id": job_id}))

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        获取任务
        :param job_id: 任务ID
        :return: 任务对象
        """
        return self._jobs.get(job_id)

    def get_jobs(self) -> List[Job]:
        """
        获取所有任务
        :return: 任务列表
        """
        return list(self._jobs.values())

    async def _scheduler_loop(self) -> None:
        """调度器主循环"""
        while self._running:
            try:
                now = datetime.now()

                # 获取需要运行的任务
                jobs_to_run = []
                async with self._lock:
                    for job in self._jobs.values():
                        if job.next_run_time and job.next_run_time <= now and job.running_instances < job.max_instances:
                            jobs_to_run.append(job)

                # 运行任务
                for job in jobs_to_run:
                    # 使用分布式锁确保任务不会重复运行
                    try:
                        async with lock_manager.lock(f"scheduler:job:{job.job_id}", timeout=10, blocking=False):
                            asyncio.create_task(job.run())
                    except Exception as e:
                        logger.error(f"Failed to acquire lock for job {job.job_id}", exc_info=e)

                # 等待一秒
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in scheduler loop", exc_info=e)
                await asyncio.sleep(5)  # 发生错误时等待较长时间

    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """
        获取调度器统计信息
        :return: 统计信息
        """
        total_jobs = len(self._jobs)
        running_jobs = sum(1 for job in self._jobs.values() if job.status == JobStatus.RUNNING)
        failed_jobs = sum(1 for job in self._jobs.values() if job.status == JobStatus.FAILED)

        return {
            "total_jobs": total_jobs,
            "running_jobs": running_jobs,
            "failed_jobs": failed_jobs,
            "is_running": self._running,
        }


# 创建默认调度器实例
scheduler = Scheduler()

# 导出
__all__ = ["scheduler", "Scheduler", "Job", "JobStatus"]
