# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：config.py
@Author  ：PySuper
@Date    ：2025-01-04 18:11
@Desc    ：Speedy config
"""
from core.cache.config.config import RedisConfig
from core.config.load.base import BaseConfig


class TaskConfig(BaseConfig):
    """
    任务配置类

    管理任务相关的所有配置参数
    """

    task_broker_db: int = 0  # Celery数据库索引
    task_result_db: int = 1  # Celery结果数据库索引
    redis_config: RedisConfig = RedisConfig()  # Redis配置

    @property
    def broker_url(self) -> str:
        """获取Celery的消息队列地址"""
        # 使用redis作为消息队列
        return f"redis://default:{self.redis_config.password}@{self.redis_config.host}:{self.redis_config.port}/{self.task_broker_db}"

    @property
    def result_backend(self) -> str:
        """获取Celery的结果存储地址"""
        # 使用redis作为结果存储
        return f"redis://default:{self.redis_config.password}@{self.redis_config.host}:{self.redis_config.port}/{self.task_result_db}"

    def __init__(self) -> None:
        """初始化任务配置"""
        super().__init__()

        # 任务队列配置
        self.queue_size: int = 1000
        self.max_retries: int = 3
        self.retry_delay: int = 60

        # 工作线程配置
        self.num_workers: int = 4
        self.worker_timeout: int = 3600

        # 任务执行配置
        self.task_timeout: int = 3600
        self.max_concurrent_tasks: int = 10

        # 监控配置
        self.enable_monitoring: bool = True
        self.stats_interval: int = 60

        # 任务重试
        self.retry_backoff_factor: int = 2  # 重试间隔
        self.retry_jitter_factor: float = 0.5  # 重试随机因子
        self.retry_max_jitter: int = 60  # 重试最大随机因子
        self.retry_backoff_max: int = 600  # 重试最大重试间隔

        # 补充配置

    async def init(self) -> None:
        """初始化配置"""
        await super().init()
        # 这里可以添加配置验证逻辑

    async def close(self) -> None:
        """关闭配置"""
        await super().close()
