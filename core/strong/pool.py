import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool as RedisPool
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config.setting import settings
from cache.exceptions import CacheError


class PoolManager:
    """连接池管理器"""

    def __init__(self):
        self._db_engine: Optional[AsyncEngine] = None
        self._db_pool: Optional[async_sessionmaker[AsyncSession]] = None
        self._redis_pool: Optional[RedisPool] = None
        self._redis_client: Optional[redis.Redis] = None
        self._last_check: Optional[datetime] = None
        self._health_check_interval = 30  # 健康检查间隔（秒）

    async def init_pools(self):
        """初始化所有连接池"""
        await self.init_db_pool()
        await self.init_redis_pool()

    async def init_db_pool(self):
        """初始化数据库连接池"""
        if self._db_engine is None:
            self._db_engine = create_async_engine(
                settings.DATABASE_URI,
                poolclass=AsyncAdaptedQueuePool,
                pool_pre_ping=True,  # 每次连接前ping
                pool_size=settings.DB_POOL_SIZE,  # 连接池大小
                max_overflow=settings.DB_MAX_OVERFLOW,  # 最大溢出连接数
                pool_timeout=settings.DB_POOL_TIMEOUT,  # 获取连接超时时间
                pool_recycle=settings.DB_POOL_RECYCLE,  # 连接回收时间
                echo=settings.DB_ECHO,  # 是否打印SQL
            )

            self._db_pool = async_sessionmaker(
                self._db_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

    async def init_redis_pool(self):
        """初始化Redis连接池"""
        if self._redis_pool is None:
            self._redis_pool = RedisPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                max_connections=settings.REDIS_POOL_SIZE,  # 最大连接数
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,  # socket超时
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,  # 连接超时
                retry_on_timeout=True,  # 超时重试
                retry=Retry(ExponentialBackoff(), settings.REDIS_MAX_RETRIES),  # 重试策略
                health_check_interval=30,  # 健康检查间隔
            )

            self._redis_client = redis.Redis(
                connection_pool=self._redis_pool,
                auto_close_connection_pool=False,
            )

    @asynccontextmanager
    async def db_session(self) -> AsyncSession:
        """获取数据库会话"""
        if self._db_pool is None:
            await self.init_db_pool()

        session: AsyncSession = self._db_pool()
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"数据库操作失败: {str(e)}")
        finally:
            await session.close()

    @property
    def redis(self) -> redis.Redis:
        """获取Redis客户端"""
        if self._redis_client is None:
            raise CacheError("Redis连接池未初始化")
        return self._redis_client

    async def check_health(self) -> dict:
        """检查连接池健康状态"""
        now = datetime.now()
        if self._last_check is not None and (now - self._last_check).total_seconds() < self._health_check_interval:
            return self._last_health_status

        status = {
            "database": {"status": "unknown", "details": None},
            "redis": {"status": "unknown", "details": None},
            "timestamp": now.isoformat(),
        }

        # 检查数据库连接
        try:
            async with self.db_session() as session:
                await session.execute("SELECT 1")
                status["database"] = {
                    "status": "healthy",
                    "pool_size": self._db_engine.pool.size(),
                    "checkedout": self._db_engine.pool.checkedout(),
                    "overflow": self._db_engine.pool.overflow(),
                }
        except Exception as e:
            status["database"] = {"status": "unhealthy", "details": str(e)}

        # 检查Redis连接
        try:
            await self.redis.ping()
            pool_info = await self.redis.connection_pool.get_info()
            status["redis"] = {
                "status": "healthy",
                "pool_size": pool_info.get("max_connections", 0),
                "active_connections": pool_info.get("active_connections", 0),
            }
        except Exception as e:
            status["redis"] = {"status": "unhealthy", "details": str(e)}

        self._last_check = now
        self._last_health_status = status
        return status

    async def close_pools(self):
        """关闭所有连接池"""
        if self._db_engine is not None:
            await self._db_engine.dispose()
            self._db_engine = None
            self._db_pool = None

        if self._redis_client is not None:
            await self._redis_client.close()
            await self._redis_pool.disconnect()
            self._redis_client = None
            self._redis_pool = None

    async def cleanup(self):
        """定期清理空闲连接"""
        while True:
            await asyncio.sleep(300)  # 每5分钟执行一次
            try:
                if self._db_engine is not None:
                    # 回收空闲连接
                    await self._db_engine.dispose()
                    await self.init_db_pool()

                if self._redis_pool is not None:
                    # 断开空闲连接
                    await self._redis_pool.disconnect(inuse_connections=False)
            except Exception:
                pass  # 忽略清理过程中的错误


# 创建全局连接池管理器实例
pool_manager = PoolManager()
