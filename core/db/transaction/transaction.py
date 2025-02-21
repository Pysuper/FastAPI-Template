from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, TypeVar, Optional

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class TransactionManager:
    """事务管理器"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._savepoint_id = 0

    @property
    def next_savepoint_id(self) -> str:
        """获取下一个保存点ID"""
        self._savepoint_id += 1
        return f"sp_{self._savepoint_id}"

    @asynccontextmanager
    async def atomic(self) -> AsyncGenerator[AsyncSession, None]:
        """原子性事务
        使用方法:
        async with transaction_manager.atomic() as session:
            await session.execute(...)
        """
        async with self.session.begin():
            try:
                yield self.session
            except Exception:
                await self.session.rollback()
                raise

    @asynccontextmanager
    async def savepoint(self) -> AsyncGenerator[AsyncSession, None]:
        """保存点事务
        使用方法:
        async with transaction_manager.savepoint() as session:
            await session.execute(...)
        """
        savepoint = await self.session.begin_nested()
        try:
            yield self.session
        except Exception:
            await savepoint.rollback()
            raise

    async def run_in_transaction(self, func: Callable[..., T], *args, **kwargs) -> T:
        """在事务中执行函数
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        async with self.atomic():
            return await func(*args, **kwargs)

    async def run_in_savepoint(self, func: Callable[..., T], *args, **kwargs) -> T:
        """在保存点中执行函数
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        async with self.savepoint():
            return await func(*args, **kwargs)


class TransactionContext:
    """事务上下文"""

    def __init__(self):
        self._transactions: list[AsyncSession] = []

    def get_current_transaction(self) -> Optional[AsyncSession]:
        """获取当前事务"""
        return self._transactions[-1] if self._transactions else None

    def push_transaction(self, transaction: AsyncSession):
        """压入事务"""
        self._transactions.append(transaction)

    def pop_transaction(self) -> Optional[AsyncSession]:
        """弹出事务"""
        return self._transactions.pop() if self._transactions else None

    @asynccontextmanager
    async def transaction(self, session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
        """事务上下文管理器"""
        self.push_transaction(session)
        try:
            yield session
        finally:
            self.pop_transaction()


transaction_context = TransactionContext()
