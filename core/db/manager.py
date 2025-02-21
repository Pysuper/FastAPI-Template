"""
数据库管理器模块

提供数据库连接和会话管理功能，包括：
    - 数据库连接池管理
    - 同步/异步会话管理
    - 事务管理
    - 健康检查
    - 连接重试机制
    - 状态监控
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Dict, Generator, Generic, Optional, TypeVar, Union

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, QueuePool

from core.db.core.config import DatabaseConfig
from core.exceptions.database.async_db import (
    AsyncConnectionException,
    AsyncEngineException,
    AsyncSessionException,
    GreenletException,
)
from core.exceptions.system.database import DatabaseException, SessionException

# 类型变量
T = TypeVar("T")
ModelType = TypeVar("ModelType")
EngineType = TypeVar("EngineType", Engine, AsyncEngine)
SessionType = TypeVar("SessionType", Session, AsyncSession)

# 配置日志记录器
logger = logging.getLogger(__name__)


class BaseSessionManager(Generic[EngineType, SessionType]):
    """
    会话管理器基类
    提供会话管理的基本功能和接口
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """
        初始化会话管理器
        :param config: 数据库配置对象
        """
        self.config = config
        self.engine: Optional[EngineType] = None
        self.session_factory: Optional[Union[sessionmaker, async_sessionmaker]] = None
        self._retry_count: int = 3
        self._retry_delay: int = 1  # 秒
        self._active_sessions: int = 0

    def _get_engine_config(self) -> Dict[str, Any]:
        """
        获取数据库引擎配置
        :return: 引擎配置字典
        """
        return {
            "poolclass": QueuePool,
            "pool_pre_ping": True,
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "pool_timeout": self.config.pool_timeout,
            "pool_recycle": self.config.pool_recycle,
            "echo": self.config.echo_sql,
            "echo_pool": self.config.echo_pool,
            "connect_args": {
                "charset": self.config.charset,
                "use_unicode": True,
                "autocommit": False,
            },
        }

    async def get_status(self) -> Dict[str, Any]:
        """
        获取连接池状态
        :return: 状态信息字典
        """
        if self.engine is None:
            return {"status": "not_initialized"}

        try:
            pool = self.engine.pool
            return {
                "status": "running",
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "active_sessions": self._active_sessions,
            }
        except Exception as e:
            logger.error(f"获取连接池状态失败: {e}")
            return {"status": "error", "error": str(e)}


class SyncSessionManager(BaseSessionManager[Engine, Session]):
    """
    同步会话管理器
    提供同步数据库操作的功能
    """

    def init(self) -> None:
        """
        初始化同步会话管理器
        :raises DatabaseException: 当初始化失败时
        """
        if self.engine is not None:
            return

        for attempt in range(self._retry_count):
            try:
                # 创建引擎
                self.engine = create_engine(
                    self.config.url.replace("+asyncmy", ""), **self._get_engine_config()  # 移除异步驱动
                )

                # 测试连接
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                # 创建会话工厂
                self.session_factory = sessionmaker(
                    bind=self.engine,
                    expire_on_commit=False,
                    autoflush=False,
                )

                logger.info("同步会话管理器初始化成功")
                return

            except (SQLAlchemyError, DBAPIError) as e:
                logger.error(f"数据库连接尝试 {attempt + 1} 失败: {e}")
                if attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                else:
                    logger.error("所有数据库连接尝试均失败")
                    raise DatabaseException(f"数据库初始化失败: {str(e)}")

    def close(self) -> None:
        """关闭同步会话管理器"""
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None
            self.session_factory = None
            logger.info("同步会话管理器已关闭")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        获取同步数据库会话
        :raises SessionException: 当会话操作失败时
        :yields: 数据库会话
        """
        if self.session_factory is None:
            raise SessionException("会话管理器未初始化")

        session = self.session_factory()
        self._active_sessions += 1
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise SessionException(f"会话操作失败: {str(e)}")
        except Exception as e:
            session.rollback()
            logger.error(f"会话中发生意外错误: {e}")
            raise
        finally:
            session.close()
            self._active_sessions -= 1

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        获取带事务的同步数据库会话
        :raises SessionException: 当事务操作失败时
        :yields: 数据库会话
        """
        with self.session() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"事务操作失败: {e}")
                raise SessionException(f"事务操作失败: {str(e)}")


class AsyncSessionManager(BaseSessionManager[AsyncEngine, AsyncSession]):
    """
    异步会话管理器
    提供异步数据库操作的功能
    """

    async def init(self) -> None:
        """
        初始化异步会话管理器
        :raises DatabaseException: 当初始化失败时
        """
        if self.engine is not None:
            return

        for attempt in range(self._retry_count):
            try:
                # 创建引擎
                engine_config = self._get_engine_config()
                engine_config["poolclass"] = AsyncAdaptedQueuePool
                self.engine = create_async_engine(self.config.url, **engine_config)

                # 测试连接
                try:
                    async with self.engine.connect() as conn:
                        await conn.execute(text("SELECT 1"))
                except Exception as e:
                    if "greenlet_spawn" in str(e):
                        raise GreenletException(
                            message="Greenlet错误",
                            details={"error": str(e)},
                            context={"attempt": attempt + 1},
                        )
                    raise AsyncConnectionException(
                        message="异步数据库连接失败",
                        details={"error": str(e)},
                        context={"attempt": attempt + 1},
                    )

                # 创建会话工厂
                self.session_factory = async_sessionmaker(
                    bind=self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False,
                )

                logger.info("异步会话管理器初始化成功")
                return

            except (SQLAlchemyError, DBAPIError) as e:
                logger.error(f"数据库连接尝试 {attempt + 1} 失败: {e}")
                if attempt < self._retry_count - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                else:
                    logger.error("所有数据库连接尝试均失败")
                    if isinstance(e, GreenletException):
                        raise e
                    raise AsyncEngineException(f"异步数据库初始化失败: {str(e)}")

    async def close(self) -> None:
        """关闭异步会话管理器"""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            logger.info("异步会话管理器已关闭")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取异步数据库会话
        :raises AsyncSessionException: 当会话操作失败时
        :yields: 异步数据库会话
        """
        if self.session_factory is None:
            raise AsyncSessionException("异步会话管理器未初始化")

        session = self.session_factory()
        self._active_sessions += 1
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"异步数据库会话错误: {e}")
            raise AsyncSessionException(f"异步会话操作失败: {str(e)}")
        except Exception as e:
            await session.rollback()
            logger.error(f"异步会话中发生意外错误: {e}")
            raise
        finally:
            await session.close()
            self._active_sessions -= 1

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取带事务的异步数据库会话
        :raises AsyncSessionException: 当事务操作失败时
        :yields: 异步数据库会话
        """
        async with self.session() as session:
            async with session.begin():
                try:
                    yield session
                except Exception as e:
                    logger.error(f"异步事务操作失败: {e}")
                    raise AsyncSessionException(f"异步事务操作失败: {str(e)}")


class DatabaseManager:
    """
    数据库管理器
    提供同步和异步数据库操作的统一接口
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """
        初始化数据库管理器
        :param config: 数据库配置对象
        """
        self.config = config
        self.sync_manager = SyncSessionManager(config)
        self.async_manager = AsyncSessionManager(config)
        self._initialized = False

    def init_sync(self) -> None:
        """初始化同步数据库管理器"""
        if not self._initialized:
            self.sync_manager.init()
            self._initialized = True
            print(" ✅ DatabaseManager sync")

    async def init_async(self) -> None:
        """初始化异步数据库管理器"""
        if not self._initialized:
            try:
                await self.async_manager.init()
                self._initialized = True
                print(" ✅ DatabaseManager Async")
            except GreenletException:
                logger.warning("异步初始化失败，尝试同步初始化")
                self.init_sync()

    async def init(self) -> None:
        """初始化数据库管理器"""
        if self._initialized:
            return

        try:
            await self.init_async()  # 先尝试异步初始化
        except GreenletException:
            logger.warning("异步初始化失败，尝试同步初始化")
            self.init_sync()  # 如果失败则尝试同步初始化
        except Exception as e:
            if isinstance(e, (AsyncConnectionException, GreenletException)):
                raise e
            raise AsyncEngineException(f"数据库初始化失败: {str(e)}")

    async def close(self) -> None:
        """关闭数据库管理器"""
        if self._initialized:
            self.sync_manager.close()
            await self.async_manager.close()
            self._initialized = False

    async def get_status(self) -> Dict[str, Any]:
        """
        获取数据库状态
        :return: 状态信息字典
        """
        sync_status = await self.sync_manager.get_status()
        async_status = await self.async_manager.get_status()
        return {"sync": sync_status, "async": async_status}

    def session(self) -> contextmanager:
        """获取同步数据库会话"""
        return self.sync_manager.session()

    def transaction(self) -> contextmanager:
        """获取同步事务会话"""
        return self.sync_manager.transaction()

    def async_session(self) -> asynccontextmanager:
        """获取异步数据库会话"""
        return self.async_manager.session()

    def async_transaction(self) -> asynccontextmanager:
        """获取异步事务会话"""
        return self.async_manager.transaction()

    async def reload(self, config: DatabaseConfig) -> None:
        """
        重新加载数据库配置
        :param config: 新的数据库配置
        """
        await self.close()
        self.config = config
        self.sync_manager = SyncSessionManager(config)
        self.async_manager = AsyncSessionManager(config)
        await self.init()


# 全局数据库管理器实例
db_manager = DatabaseManager(DatabaseConfig())
