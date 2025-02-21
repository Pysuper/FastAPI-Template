import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import AsyncAdaptedQueuePool

logger = logging.getLogger(__name__)


class PoolStats:
    """连接池统计信息"""

    def __init__(self):
        self.created_at = datetime.now()
        self.total_connections = 0
        self.active_connections = 0
        self.idle_connections = 0
        self.waiting_connections = 0
        self.max_connections = 0
        self.min_connections = 0
        self.connection_timeouts = 0
        self.last_reset = None

    def to_dict(self) -> Dict:
        return {
            "created_at": self.created_at.isoformat(),
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "waiting_connections": self.waiting_connections,
            "max_connections": self.max_connections,
            "min_connections": self.min_connections,
            "connection_timeouts": self.connection_timeouts,
            "last_reset": self.last_reset.isoformat() if self.last_reset else None,
        }


class ConnectionPoolManager:
    """连接池管理器"""

    def __init__(
        self,
        engine: AsyncEngine,
        min_size: int = 5,
        max_size: int = 20,
        idle_timeout: int = 300,
        max_lifetime: int = 3600,
        health_check_interval: int = 30,
    ):
        self.engine = engine
        self.pool = engine.pool
        if not isinstance(self.pool, AsyncAdaptedQueuePool):
            raise ValueError("Engine must use AsyncAdaptedQueuePool")

        self.min_size = min_size
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        self.max_lifetime = max_lifetime
        self.health_check_interval = health_check_interval

        self.stats = PoolStats()
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动连接池管理器"""
        self._monitor_task = asyncio.create_task(self._monitor_pool())
        self._cleanup_task = asyncio.create_task(self._cleanup_idle_connections())
        logger.info("Connection pool manager started")

    async def stop(self):
        """停止连接池���理器"""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None

        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

        await self.engine.dispose()
        logger.info("Connection pool manager stopped")

    async def _monitor_pool(self):
        """监控连接池状态"""
        while True:
            try:
                self.stats.total_connections = self.pool.size()
                self.stats.active_connections = self.pool.checkedout()
                self.stats.idle_connections = self.pool.checkedin()
                self.stats.waiting_connections = self.pool.overflow()

                if self.stats.total_connections > self.stats.max_connections:
                    self.stats.max_connections = self.stats.total_connections
                if self.stats.total_connections < self.stats.min_connections:
                    self.stats.min_connections = self.stats.total_connections

                # 记录异常情况
                if self.stats.active_connections > self.max_size:
                    logger.warning(
                        f"Active connections ({self.stats.active_connections}) exceeded max size ({self.max_size})"
                    )

                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring pool: {e}")
                await asyncio.sleep(5)

    async def _cleanup_idle_connections(self):
        """清理空闲连接"""
        while True:
            try:
                # 获取当前时间
                now = datetime.now()

                # 如果空闲连接数量大于最小连接数
                if self.stats.idle_connections > self.min_size:
                    # 获取所有空闲连接
                    idle_connections = [
                        conn
                        for conn in self.pool._pool
                        if (now - conn.info["created_at"]).total_seconds() > self.idle_timeout
                    ]

                    # 关闭超时的空闲连接
                    for conn in idle_connections:
                        if self.stats.idle_connections > self.min_size:
                            await conn.close()
                            self.stats.idle_connections -= 1

                await asyncio.sleep(60)  # 每分钟检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error cleaning up idle connections: {e}")
                await asyncio.sleep(5)

    def get_stats(self) -> Dict:
        """获取连接池统计信息"""
        return self.stats.to_dict()

    async def reset_stats(self):
        """重置统计信息"""
        self.stats = PoolStats()
        self.stats.last_reset = datetime.now()

    async def resize_pool(self, min_size: Optional[int] = None, max_size: Optional[int] = None):
        """调整连接池大小"""
        if min_size is not None:
            self.min_size = min_size
        if max_size is not None:
            self.max_size = max_size

        # 更新连接池配置
        self.pool._pool.maxsize = self.max_size
        logger.info(f"Pool resized: min_size={self.min_size}, max_size={self.max_size}")

    async def health_check(self) -> bool:
        """连接池健康检查"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
