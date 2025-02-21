"""
@Project ：Speedy
@File    ：session.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：数据库会话管理模块

提供了数据库会话管理的核心功能，包括:
    - 同步/异步会话管理
    - 读写分离支持
    - 连接池管理
    - 事务管理
    - 会话生命周期管理
    - 异常处理
    - 配置管理
"""

import asyncio
import json
import logging
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Generator,
    List,
    Optional,
    TypeVar,
)

from sqlalchemy import AsyncAdaptedQueuePool, text
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from core.config.setting import settings

from exceptions.system.database import SessionException, TransactionException

# 配置日志记录器
logger = logging.getLogger(__name__)

# 类型变量定义
T = TypeVar("T")
SessionType = TypeVar("SessionType", Session, AsyncSession)
EngineType = TypeVar("EngineType", Engine, AsyncEngine)


class DatabaseConfig:
    """
    数据库配置类
    用于统一管理数据库配置参数，提供类型安全和参数验证
    """

    def __init__(self, settings: Any) -> None:
        """
        初始化数据库配置
        :param settings: 配置对象
        :raises ValueError: 当缺少必需的配置项时
        """
        self.settings = settings
        self._validate_config()

    def _validate_config(self) -> None:
        """
        验证配置参数的完整性和有效性
        :raises ValueError: 当配置参数无效或缺失时
        """
        required_fields = [
            "host",
            "port",
            "username",
            "password",
            "database",
            "pool_size",
            "max_overflow",
            "pool_timeout",
            "pool_recycle",
        ]
        for field in required_fields:
            if not hasattr(self.settings.db, field):
                raise ValueError(f"缺少必需的配置项==>: {field}")

        # 验证配置值的有效性
        if self.settings.db.pool_size <= 0:
            raise ValueError("连接池大小必须大于0")
        if self.settings.db.max_overflow < 0:
            raise ValueError("最大溢出连接数不能为负数")
        if self.settings.db.pool_timeout <= 0:
            raise ValueError("连接池超时时间必须大于0")

    @property
    def write_url(self) -> str:
        """主库连接URL"""
        return self.settings.db.write_url

    @property
    def read_urls(self) -> List[str]:
        """从库连接URL列表"""
        return self.settings.db.read_urls

    @property
    def pool_size(self) -> int:
        """连接池大小"""
        return self.settings.db.pool_size

    @property
    def max_overflow(self) -> int:
        """最大溢出连接数"""
        return self.settings.db.max_overflow

    @property
    def pool_timeout(self) -> int:
        """连接池超时时间（秒）"""
        return self.settings.db.pool_timeout

    @property
    def pool_recycle(self) -> int:
        """连接回收时间（秒）"""
        return self.settings.db.pool_recycle

    @property
    def echo_sql(self) -> bool:
        """是否打印SQL语句"""
        return self.settings.db.echo_sql

    @property
    def echo_pool(self) -> bool:
        """是否打印连接池信息"""
        return self.settings.db.echo_pool

    @property
    def pool_pre_ping(self) -> bool:
        """是否在获取连接前进行ping测试"""
        return self.settings.db.pool_pre_ping

    def get_engine_config(self, is_async: bool = False) -> dict:
        """获取数据库引擎配置"""
        config = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": self.echo_sql,
            "echo_pool": self.echo_pool,
        }

        if is_async:
            # 异步连接特定配置
            config.update(
                {
                    "poolclass": AsyncAdaptedQueuePool,
                }
            )
        else:
            # 同步连接特定配置
            config.update(
                {
                    "poolclass": QueuePool,
                }
            )

        return config


class BaseSessionManager:
    """
    会话管理器基类
    提供会话管理的基础功能和公共接口
    """

    def __init__(self) -> None:
        """
        初始化会话管理器
        设置初始状态和加载配置
        """
        self._initialized: bool = False
        self._config: Optional[DatabaseConfig] = None
        self._retry_count: int = 0
        self._setup_logging()

    def _setup_logging(self) -> None:
        """配置日志记录器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(logging.INFO)

    @property
    def config(self) -> DatabaseConfig:
        """
        获取数据库配置
        :return: 数据库配置对象
        :raises RuntimeError: 当配置未初始化时
        """
        if self._config is None:
            self._config = DatabaseConfig(settings)
        return self._config

    def _check_initialized(self) -> None:
        """
        检查是否已初始化
        :raises SessionError: 当会话管理器未初始化时
        """
        if not self._initialized:
            raise SessionException("会话管理器尚未初始化")

    def _handle_retry(self, error: Exception, operation: str) -> None:
        """
        处理操作重试逻辑
        :param error: 捕获的异常
        :param operation: 操作描述
        :raises Exception: 当重试次数超过限制时抛出原始异常
        """
        self._retry_count += 1
        if self._retry_count > self.config.max_retries:
            self.logger.error(f"{operation}失败，已达到最大重试次数: {error}")
            self._retry_count = 0
            raise error

        self.logger.warning(f"{operation}失败，正在进行第{self._retry_count}次重试: {error}")
        time.sleep(self.config.retry_interval)

    def _reset_retry_count(self) -> None:
        """重置重试计数器"""
        self._retry_count = 0

    async def _health_check(self) -> bool:
        """
        检查数据库连接健康状态
        :return: 连接是否健康
        """
        raise NotImplementedError("子类必须实现健康检查方法")

    def _log_operation(self, operation: str, **kwargs: Any) -> None:
        """
        记录数据库操作日志
        :param operation: 操作描述
        :param kwargs: 额外的日志信息
        """
        log_data = {"operation": operation, "timestamp": datetime.now().isoformat(), **kwargs}
        self.logger.info(f"数据库操作: {json.dumps(log_data, ensure_ascii=False)}")


class SyncDatabaseManager(BaseSessionManager):
    """
    同步数据库管理器
    提供同步数据库操作的功能，包括连接管理、会话管理和事务管理
    """

    _instance: Optional["SyncDatabaseManager"] = None

    def __new__(cls) -> "SyncDatabaseManager":
        """
        实现单例模式
        :return: SyncDatabaseManager实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化同步数据库管理器"""
        if not hasattr(self, "_initialized"):
            super().__init__()
            self.engine: Optional[Engine] = None
            self.session_factory: Optional[sessionmaker] = None
            self._active_sessions: int = 0
            self._lock = threading.Lock()

    def init(self) -> None:
        """
        初始化数据库管理器
        :raises ConnectionError: 当数据库连接失败时
        """
        if self._initialized:
            return

        try:
            # 创建数据库引擎
            engine_config = self.config.get_engine_config(is_async=False)
            self.engine = create_engine(self.config.write_url, **engine_config)

            # 创建会话工厂
            self.session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine, expire_on_commit=False
            )

            self._initialized = True
            self.logger.info("同步数据库管理器初始化成功")
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise ConnectionError(f"数据库连接失败: {str(e)}")

    def _health_check(self) -> bool:
        """
        检查数据库连接健康状态
        :return: 连接是否健康
        """
        if not self._initialized or not self.engine:
            return False

        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error(f"数据库健康检查失败: {e}")
            return False

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话的上下文管理器
        :return: 数据库会话
        :raises SessionError: 当会话操作失败时
        """
        if not self._initialized:
            self.init()

        session = self.session_factory()
        self._active_sessions += 1
        self.logger.debug(f"创建新会话，当前活动会话数: {self._active_sessions}")

        try:
            yield session
        except Exception as e:
            self.logger.error(f"会话操作失败: {e}")
            session.rollback()
            raise SessionException(f"会话操作失败: {str(e)}")
        finally:
            session.close()
            self._active_sessions -= 1
            self.logger.debug(f"关闭会话，当前活动会话数: {self._active_sessions}")

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        事务上下文管理器
        :return: 数据库会话
        :raises TransactionError: 当事务操作失败时
        """
        with self.session() as session:
            try:
                yield session
                session.commit()
                self.logger.debug("事务提交成功")
            except Exception as e:
                session.rollback()
                self.logger.error(f"事务操作失败: {e}")
                raise TransactionException(f"事务操作失败: {str(e)}")

    def execute_in_transaction(self, func: Callable[[Session], T], *args: Any, **kwargs: Any) -> T:
        """
        在事务中执行函数
        :param func: 要执行的函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 函数执行结果
        :raises TransactionError: 当事务执行失败时
        """
        with self.transaction() as session:
            try:
                result = func(session)
                return result
            except Exception as e:
                raise TransactionException(f"事务执行失败: {str(e)}")

    def dispose(self) -> None:
        """
        释放所有数据库连接
        """
        if self._initialized and self.engine:
            with self._lock:
                self.engine.dispose()
                self._initialized = False
                self.logger.info("同步数据库连接已释放")

    def __del__(self) -> None:
        """析构函数，确保资源被正确释放"""
        self.dispose()


class AsyncDatabaseManager(BaseSessionManager):
    """
    异步数据库管理器
    实现读写分离和连接池管理，提供异步数据库操作功能
    """

    _instance: Optional["AsyncDatabaseManager"] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "AsyncDatabaseManager":
        """单例模式"""
        if not cls._instance:

            async def create_instance():
                async with cls._lock:
                    if not cls._instance:
                        cls._instance = super().__new__(cls)
                        await cls._instance.init()
                return cls._instance

            # 在异步上下文中创建实例
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return loop.create_task(create_instance())
            else:
                return loop.run_until_complete(create_instance())
        return cls._instance

    def __init__(self) -> None:
        """初始化异步数据库管理器"""
        if not hasattr(self, "_initialized"):
            super().__init__()
            self._write_engine: Optional[AsyncEngine] = None
            self._read_engines: List[AsyncEngine] = []
            self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
            self._initialized = False

    async def init(self) -> None:
        """初始化数据库连接"""
        if self._initialized:
            return

        try:
            # 创建写库引擎
            engine_config = self.config.get_engine_config(is_async=True)
            self._write_engine = create_async_engine(
                self.config.write_url,
                **engine_config,
                poolclass=QueuePool,
            )

            # 创建读库引擎
            for url in self.config.read_urls:
                read_engine = create_async_engine(
                    url,
                    **engine_config,
                    poolclass=QueuePool,
                )
                self._read_engines.append(read_engine)

            # 创建会话工厂
            self._session_factory = async_sessionmaker(
                bind=self._write_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            # 测试连接
            async with self._write_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            self._initialized = True
            logger.info("异步数据库管理器初始化成功")

        except Exception as e:
            logger.error(f"初始化异步数据库管理器失败: {e}")
            if self._write_engine:
                await self._write_engine.dispose()
            for engine in self._read_engines:
                await engine.dispose()
            raise

    @asynccontextmanager
    async def session(self, *, for_write: bool = False) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话
        :param for_write: 是否用于写操作
        :return: 异步会话生成器
        """
        if not self._initialized:
            await self.init()

        session = self._session_factory()
        try:
            if not for_write and self._read_engines:
                # 使用读库引擎
                read_engine = self._read_engines[0]  # TODO: 实现负载均衡
                session.bind = read_engine

            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取事务会话
        :return: 异步会话生成器
        """
        if not self._initialized:
            await self.init()

        session = self._session_factory()
        try:
            async with session.begin():
                yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._write_engine:
            await self._write_engine.dispose()
        for engine in self._read_engines:
            await engine.dispose()
        self._initialized = False
        logger.info("异步数据库管理器已关闭")

    async def __aenter__(self) -> "AsyncDatabaseManager":
        """异步上下文管理器入口"""
        if not self._initialized:
            await self.init()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口"""
        await self.close()


# 创建数据库管理器实例
sync_db_manager = SyncDatabaseManager()
async_db_manager = AsyncDatabaseManager()
