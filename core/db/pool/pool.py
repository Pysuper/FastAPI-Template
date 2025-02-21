"""
数据库连接池管理器
"""
import asyncio
import logging
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from core.config.setting import get_settings
from core.db.core.manager import DatabaseConfig

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()


class DatabasePool:
    """数据库连接池管理器"""

    def __init__(self):
        self._engines: Dict[str, AsyncEngine] = {}
        self._session_factories: Dict[str, async_sessionmaker] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def init(self) -> None:
        """初始化数据库连接池"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                # 创建主数据库引擎
                main_config = DatabaseConfig()
                main_engine = await self._create_engine(
                    "main",
                    main_config,
                )
                self._engines["main"] = main_engine
                self._session_factories["main"] = async_sessionmaker(
                    main_engine, expire_on_commit=False, class_=AsyncSession
                )

                # 如果配置了读写分离，创建只读数据库引擎
                if settings.DATABASE_READ_REPLICAS:
                    for i, replica in enumerate(settings.DATABASE_READ_REPLICAS):
                        name = f"read_{i}"
                        read_config = DatabaseConfig(
                            host=replica.get("host"),
                            port=replica.get("port"),
                            username=replica.get("username"),
                            password=replica.get("password"),
                            database=replica.get("database"),
                        )
                        read_engine = await self._create_engine(
                            name,
                            read_config,
                        )
                        self._engines[name] = read_engine
                        self._session_factories[name] = async_sessionmaker(
                            read_engine, expire_on_commit=False, class_=AsyncSession
                        )

                self._initialized = True
                logger.info("Database connection pools initialized successfully")

            except Exception as e:
                logger.error("Failed to initialize database pools", exc_info=e)
                raise

    async def _create_engine(
        self,
        name: str,
        config: DatabaseConfig,
    ) -> AsyncEngine:
        """创建数据库引擎"""
        try:
            engine = create_async_engine(
                config.url,
                pool_pre_ping=True,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_timeout=config.pool_timeout,
                pool_recycle=config.pool_recycle,
                echo=config.echo,
            )
            logger.info(f"Created database engine for {name}")
            return engine
        except Exception as e:
            logger.error(f"Failed to create database engine for {name}", exc_info=e)
            raise

    async def close(self) -> None:
        """关闭所有连接池"""
        if not self._initialized:
            return

        async with self._lock:
            if not self._initialized:
                return

            for name, engine in self._engines.items():
                try:
                    await engine.dispose()
                    logger.info(f"Closed database engine for {name}")
                except Exception as e:
                    logger.error(f"Error closing database engine for {name}", exc_info=e)

            self._engines.clear()
            self._session_factories.clear()
            self._initialized = False

    def get_session_factory(self, name: str = "main") -> Optional[async_sessionmaker]:
        """获取会话工厂"""
        return self._session_factories.get(name)

    def get_engine(self, name: str = "main") -> Optional[AsyncEngine]:
        """获取数据库引擎"""
        return self._engines.get(name)

    async def get_status(self) -> Dict[str, dict]:
        """获取所有连接池状态"""
        status = {}
        for name, engine in self._engines.items():
            pool = engine.pool
            status[name] = {
                "size": pool.size(),
                "checked_out": pool.checkedin(),
                "overflow": pool.overflow(),
                "checkedout": pool.checkedout(),
            }
        return status


# 创建默认数据库连接池管理器实例
db_pool = DatabasePool()

# 导出
__all__ = ["db_pool", "DatabasePool"]
