from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from core.strong.pool import pool_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with pool_manager.db_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_with_lock() -> AsyncGenerator[AsyncSession, None]:
    """获取带锁的数据库会话"""
    async with pool_manager.db_session() as session:
        try:
            # 开启事务
            await session.begin()
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
