"""
数据库事务管理模块
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from core.db.session.manager import session_manager

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")


class TransactionManager:
    """事务管理器"""

    def __init__(self):
        self.session_manager = session_manager

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """事务上下文管理器"""
        async with self.session_manager.transaction() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Transaction failed: {e}")
                await session.rollback()
                raise

    async def atomic(self, func: Callable[..., T], *args, **kwargs) -> T:
        """原子操作装饰器"""
        async with self.transaction() as session:
            return await func(session, *args, **kwargs)

    @asynccontextmanager
    async def savepoint(self, name: Optional[str] = None) -> AsyncGenerator[None, None]:
        """保存点上下文管理器"""
        if not hasattr(self.session_manager, "_session") or self.session_manager._session is None:
            raise RuntimeError("No active transaction")

        session = self.session_manager._session
        savepoint = await session.begin_nested()
        try:
            yield
            await savepoint.commit()
        except Exception as e:
            logger.error(f"Savepoint failed: {e}")
            await savepoint.rollback()
            raise

    async def run_in_transaction(self, func: Callable[..., T], *args, **kwargs) -> T:
        """在事务中执行函数"""
        return await self.atomic(func, *args, **kwargs)


# 全局事务管理器实例
transaction_manager = TransactionManager()

# 导出
__all__ = ["transaction_manager", "TransactionManager"] 