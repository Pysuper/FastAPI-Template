"""
动态连接池
"""

import asyncio
import logging
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config.load.db import DatabaseConfig
from core.config.setting import get_settings

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()


class PoolMetrics:
    """连接池指标"""

    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.idle_connections = 0
        self.waiting_connections = 0
        self.total_queries = 0
        self.query_duration_total = 0.0
        self.last_scale_time = 0.0

    def update(self, pool):
        """更新指标"""
        self.total_connections = pool.size()
        self.active_connections = pool.checkedout()
        self.idle_connections = pool.checkedin()
        self.waiting_connections = pool.overflow()

    def record_query(self, duration: float):
        """记录查询"""
        self.total_queries += 1
        self.query_duration_total += duration


class DynamicPool:
    """动态连接池"""

    def __init__(
        self,
        config: DatabaseConfig,
        min_size: int = 5,
        max_size: int = 20,
        target_utilization: float = 0.7,  # 目标利用率
        scale_up_threshold: float = 0.8,  # 扩容阈值
        scale_down_threshold: float = 0.3,  # 缩容阈值
        scale_step: int = 2,  # 每次扩缩容步长
        scale_cooldown: int = 60,  # 扩缩容冷却时间（秒）
        metrics_interval: int = 5,  # 指标收集间隔（秒）
    ):
        self.config = config
        self.min_size = min_size
        self.max_size = max_size
        self.target_utilization = target_utilization
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.scale_step = scale_step
        self.scale_cooldown = scale_cooldown
        self.metrics_interval = metrics_interval

        self.engine: Optional[AsyncEngine] = None
        self.metrics = PoolMetrics()
        self._monitor_task: Optional[asyncio.Task] = None
        self._scaler_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动连接池"""
        # 创建引擎
        self.engine = create_async_engine(
            self.config.url,
            poolclass=AsyncAdaptedQueuePool,
            pool_pre_ping=True,
            pool_size=self.min_size,
            max_overflow=self.max_size - self.min_size,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            echo=self.config.echo,
        )

        # 启动监控任务
        self._monitor_task = asyncio.create_task(self._monitor_metrics())
        self._scaler_task = asyncio.create_task(self._auto_scale())

        logger.info(f"Dynamic pool started with size: {self.min_size}")

    async def stop(self):
        """停止连接池"""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None

        if self._scaler_task:
            self._scaler_task.cancel()
            self._scaler_task = None

        if self.engine:
            await self.engine.dispose()
            self.engine = None

        logger.info("Dynamic pool stopped")

    async def _monitor_metrics(self):
        """监控指标"""
        while True:
            try:
                if self.engine and self.engine.pool:
                    self.metrics.update(self.engine.pool)
            except Exception as e:
                logger.error("Failed to update metrics", exc_info=e)

            await asyncio.sleep(self.metrics_interval)

    async def _auto_scale(self):
        """自动扩缩容"""
        while True:
            try:
                if self.engine and self.engine.pool:
                    pool = self.engine.pool
                    current_size = pool.size()
                    active_connections = pool.checkedout()
                    utilization = active_connections / current_size if current_size > 0 else 0

                    # 扩容
                    if (
                        utilization >= self.scale_up_threshold
                        and current_size < self.max_size
                        and asyncio.get_event_loop().time() - self.metrics.last_scale_time > self.scale_cooldown
                    ):
                        new_size = min(current_size + self.scale_step, self.max_size)
                        await self._resize_pool(new_size)
                        self.metrics.last_scale_time = asyncio.get_event_loop().time()
                        logger.info(f"Pool scaled up to {new_size}")

                    # 缩容
                    elif (
                        utilization <= self.scale_down_threshold
                        and current_size > self.min_size
                        and asyncio.get_event_loop().time() - self.metrics.last_scale_time > self.scale_cooldown
                    ):
                        new_size = max(current_size - self.scale_step, self.min_size)
                        await self._resize_pool(new_size)
                        self.metrics.last_scale_time = asyncio.get_event_loop().time()
                        logger.info(f"Pool scaled down to {new_size}")

            except Exception as e:
                logger.error("Failed to auto scale", exc_info=e)

            await asyncio.sleep(self.metrics_interval)

    async def _resize_pool(self, new_size: int):
        """调整连接池大小"""
        if not self.engine:
            return

        try:
            # 创建新引擎
            new_engine = create_async_engine(
                self.config.url,
                poolclass=AsyncAdaptedQueuePool,
                pool_pre_ping=True,
                pool_size=new_size,
                max_overflow=self.max_size - new_size,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo,
            )

            # 等待所有连接释放
            old_engine = self.engine
            self.engine = new_engine

            # 关闭旧引擎
            await old_engine.dispose()

        except Exception as e:
            logger.error("Failed to resize pool", exc_info=e)
            raise

    async def get_status(self) -> Dict[str, int]:
        """获取连接池状态"""
        if not self.engine or not self.engine.pool:
            return {
                "status": "not_initialized",
                "total_connections": 0,
                "active_connections": 0,
                "idle_connections": 0,
                "waiting_connections": 0,
            }

        pool = self.engine.pool
        return {
            "status": "running",
            "total_connections": pool.size(),
            "active_connections": pool.checkedout(),
            "idle_connections": pool.checkedin(),
            "waiting_connections": pool.overflow(),
        }
