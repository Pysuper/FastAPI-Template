# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：engine.py
@Author  ：PySuper
@Date    ：2025-01-05 13:36
@Desc    ：Speedy engine
"""
import asyncio
from contextlib import asynccontextmanager
from typing import (
    AsyncGenerator,
    Generator,
)

from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from core.config.setting import settings
from core.loge.manager import logic as logger
from db.core.session import sync_db_manager
from exceptions.system.database import SessionException, TransactionException

# 创建数据库引擎
engine = create_engine(
    settings.db.write_url,
    poolclass=QueuePool,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_timeout=settings.db.pool_timeout,
    pool_recycle=settings.db.pool_recycle,
    pool_pre_ping=True,
    echo=settings.db.echo_sql,
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_sync_db() -> Generator[Session, None, None]:
    """
    获取同步数据库会话的依赖函数
    :return: 同步数据库会话
    :raises SessionError: 当会话操作失败时
    """
    with sync_db_manager.session() as session:
        yield session


'''
# async def get_async_db(*, for_write: bool = False) -> AsyncGenerator[AsyncSession, None]:
#     """
#     获取异步数据库会话
#     :param for_write: 是否用于写操作
#     :return: 异步会话生成器
#     """
#     manager = AsyncDatabaseManager()
#     try:
#         await manager.init()  # 确保初始化完成
#         async with manager.session(for_write=for_write) as session:
#             yield session
#     except Exception as e:
#         logger.error(f"数据库会话异常: {e}")
#         await session.rollback()
#         raise
#     finally:
#         await session.close()
#         await manager.close()
#
#
# @asynccontextmanager
# async def get_db_with_transaction() -> AsyncGenerator[AsyncSession, None]:
#     """
#     获取带事务的数据库会话
#     :return: 异步会话生成器
#     """
#     manager = AsyncDatabaseManager()
#     try:
#         await manager.init()  # 确保初始化完成
#         async with manager.transaction() as session:
#             yield session
#     except Exception as e:
#         logger.error(f"事务会话异常: {e}")
#         if session.in_transaction():
#             await session.rollback()
#         raise TransactionException(f"事务会话异常: {str(e)}")
#     finally:
#         await session.close()
#         await manager.close()
#
#
# @asynccontextmanager
# async def get_db_with_lock() -> AsyncGenerator[AsyncSession, None]:
#     """
#     获取带锁的异步数据库会话
#     :return: 异步数据库会话
#     :raises SessionError: 当会话操作失败时
#     """
#     manager = AsyncDatabaseManager()
#     try:
#         await manager.init()  # 确保初始化完成
#         async with manager.transaction() as session:
#             # 获取分布式锁
#             yield session
#     except Exception as e:
#         logger.error(f"带锁会话异常: {e}")
#         if session.in_transaction():
#             await session.rollback()
#         raise SessionException(f"带锁会话操作失败: {str(e)}")

'''


# 创建异步引擎
async_engine = create_async_engine(
    settings.db.write_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_timeout=settings.db.pool_timeout,
    pool_recycle=settings.db.pool_recycle,
    pool_pre_ping=True,
    echo=settings.db.echo_sql,
    future=True,
    pool_use_lifo=True,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# 创建异步作用域会话
async_session = async_scoped_session(AsyncSessionLocal, scopefunc=asyncio.current_task)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话
    :return: 异步会话生成器
    """
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"数据库会话异常: {e}")
        await session.rollback()
        raise SessionException(f"数据库会话异常: {str(e)}")
    finally:
        await session.close()


@asynccontextmanager
async def get_async_db_with_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    获取带事务的数据库会话
    :return: 异步会话生成器
    """
    session = AsyncSessionLocal()
    try:
        async with session.begin():
            yield session
    except Exception as e:
        logger.error(f"事务会话异常: {e}")
        await session.rollback()
        raise TransactionException(f"事务会话异常: {str(e)}")
    finally:
        await session.close()


@asynccontextmanager
async def get_async_db_with_lock() -> AsyncGenerator[AsyncSession, None]:
    """
    获取带锁的异步数据库会话
    :return: 异步数据库会话
    :raises SessionError: 当会话操作失败时
    """
    session = AsyncSessionLocal()
    try:
        async with session.begin():
            # 获取分布式锁
            yield session
    except Exception as e:
        logger.error(f"带锁会话异常: {e}")
        await session.rollback()
        raise SessionException(f"带锁会话操作失败: {str(e)}")
    finally:
        await session.close()
