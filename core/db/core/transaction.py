"""
@Project ：Speedy
@File    ：transaction.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：数据库事务管理模块

提供了数据库事务管理的核心功能，包括:
    - 原子性事务
    - 保存点事务
    - 事务嵌套
    - 事务上下文
    - 事务装饰器
"""

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    List,
    Optional,
    TypeVar,
)

from sqlalchemy.ext.asyncio import AsyncSession

from core.db.core.session import TransactionError

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")
R = TypeVar("R")


class TransactionState(Enum):
    """事务状态"""

    INACTIVE = auto()  # 未激活
    ACTIVE = auto()  # 活动中
    COMMITTED = auto()  # 已提交
    ROLLED_BACK = auto()  # 已回滚
    FAILED = auto()  # 失败


@dataclass
class SavePoint:
    """
    保存点
    用于在事务中创建检查点
    """

    name: str
    state: TransactionState = TransactionState.ACTIVE
    parent: Optional["SavePoint"] = None
    children: List["SavePoint"] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.children is None:
            self.children = []


class TransactionManager:
    """
    事务管理器
    提供事务管理的核心功能
    """

    def __init__(self, session: AsyncSession):
        """
        初始化事务管理器
        :param session: 数据库会话
        """
        self.session = session
        self._savepoint_id = 0
        self._current_savepoint: Optional[SavePoint] = None
        self._state = TransactionState.INACTIVE

    @property
    def next_savepoint_id(self) -> str:
        """
        获取下一个保存点ID
        :return: 保存点ID
        """
        self._savepoint_id += 1
        return f"sp_{self._savepoint_id}"

    @property
    def is_active(self) -> bool:
        """
        检查事务是否处于活动状态
        :return: 是否活动
        """
        return self._state == TransactionState.ACTIVE

    async def begin(self) -> None:
        """
        开始事务
        :raises TransactionError: 当事务已经开始时
        """
        if self.is_active:
            raise TransactionError("事务已经开始")

        try:
            await self.session.begin()
            self._state = TransactionState.ACTIVE
        except Exception as e:
            self._state = TransactionState.FAILED
            raise TransactionError(f"开始事务失败: {str(e)}")

    async def commit(self) -> None:
        """
        提交事务
        :raises TransactionError: 当事务未开始或提交失败时
        """
        if not self.is_active:
            raise TransactionError("没有活动的事务")

        try:
            await self.session.commit()
            self._state = TransactionState.COMMITTED
        except Exception as e:
            self._state = TransactionState.FAILED
            raise TransactionError(f"提交事务失败: {str(e)}")

    async def rollback(self) -> None:
        """
        回滚事务
        :raises TransactionError: 当事务未开始或回滚失败时
        """
        if not self.is_active:
            raise TransactionError("没有活动的事务")

        try:
            await self.session.rollback()
            self._state = TransactionState.ROLLED_BACK
        except Exception as e:
            self._state = TransactionState.FAILED
            raise TransactionError(f"回滚事务失败: {str(e)}")

    @asynccontextmanager
    async def atomic(self) -> AsyncGenerator[AsyncSession, None]:
        """
        原子性事务上下文管理器
        使用方法:
        async with transaction_manager.atomic() as session:
            await session.execute(...)

        :return: 数据库会话
        :raises TransactionError: 当事务操作失败时
        """
        if self.is_active:
            yield self.session
            return

        try:
            await self.begin()
            yield self.session
            await self.commit()
        except Exception as e:
            await self.rollback()
            raise TransactionError(f"原子性事务失败: {str(e)}")

    @asynccontextmanager
    async def savepoint(self, name: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
        """
        保存点上下文管理器
        使用方法:
        async with transaction_manager.savepoint("my_savepoint") as session:
            await session.execute(...)

        :param name: 保存点名称
        :return: 数据库会话
        :raises TransactionError: 当保存点操作失败时
        """
        if not self.is_active:
            raise TransactionError("保存点必须在事务中创建")

        sp_name = name or self.next_savepoint_id
        savepoint = SavePoint(name=sp_name, parent=self._current_savepoint)

        if self._current_savepoint:
            self._current_savepoint.children.append(savepoint)

        self._current_savepoint = savepoint

        try:
            sp = await self.session.begin_nested()
            yield self.session
            await sp.commit()
            savepoint.state = TransactionState.COMMITTED
        except Exception as e:
            await sp.rollback()
            savepoint.state = TransactionState.ROLLED_BACK
            raise TransactionError(f"保存点操作失败: {str(e)}")
        finally:
            self._current_savepoint = savepoint.parent

    async def run_in_transaction(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        在事务中执行函数
        :param func: 要执行的函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 函数执行结果
        :raises TransactionError: 当函数执行失败时
        """
        async with self.atomic():
            try:
                return await func(self.session, *args, **kwargs)
            except Exception as e:
                raise TransactionError(f"事务中函数执行失败: {str(e)}")

    async def run_in_savepoint(
        self, func: Callable[..., T], name: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> T:
        """
        在保存点中执行函数
        :param func: 要执行的函数
        :param name: 保存点名称
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 函数执行结果
        :raises TransactionError: 当函数执行失败时
        """
        async with self.savepoint(name):
            try:
                return await func(self.session, *args, **kwargs)
            except Exception as e:
                raise TransactionError(f"保存点中函数执行失败: {str(e)}")


class TransactionContext:
    """
    事务上下文
    管理事务的生命周期和状态
    """

    def __init__(self):
        """初始化事务上下文"""
        self._transactions: List[AsyncSession] = []
        self._state = TransactionState.INACTIVE

    @property
    def is_active(self) -> bool:
        """
        检查是否有活动的事务
        :return: 是否有活动事务
        """
        return bool(self._transactions) and self._state == TransactionState.ACTIVE

    def get_current_transaction(self) -> Optional[AsyncSession]:
        """
        获取当前事务
        :return: 当前事务会话或None
        """
        return self._transactions[-1] if self._transactions else None

    def push_transaction(self, transaction: AsyncSession) -> None:
        """
        压入事务
        :param transaction: 事务会话
        """
        self._transactions.append(transaction)
        self._state = TransactionState.ACTIVE

    def pop_transaction(self) -> Optional[AsyncSession]:
        """
        弹出事务
        :return: 事务会话或None
        """
        if self._transactions:
            self._state = TransactionState.INACTIVE
            return self._transactions.pop()
        return None

    @asynccontextmanager
    async def transaction(self, session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
        """
        事务上下文管理器
        :param session: 数据库会话
        :return: 数据库会话
        :raises TransactionError: 当事务操作失败时
        """
        self.push_transaction(session)
        try:
            yield session
        finally:
            self.pop_transaction()


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    事务上下文管理器
    用法:
    async with transaction(session) as tx:
        await tx.execute(...)
        await tx.commit()

    :param session: 数据库会话
    :return: 数据库会话
    :raises TransactionError: 当事务操作失败时
    """
    transaction = await session.begin()
    try:
        yield session
        await transaction.commit()
    except Exception as e:
        await transaction.rollback()
        raise TransactionError(f"事务操作失败: {str(e)}")
    finally:
        await session.close()


async def atomic(session: AsyncSession, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    原子操作装饰器
    用法:
    result = await atomic(session, some_operation, arg1, arg2, kwarg1=value1)

    :param session: 数据库会话
    :param operation: 要执行的操作
    :param args: 位置参数
    :param kwargs: 关键字参数
    :return: 操作结果
    :raises TransactionError: 当操作失败时
    """
    async with transaction(session) as tx:
        try:
            result = await operation(tx, *args, **kwargs)
            return result
        except Exception as e:
            raise TransactionError(f"原子操作失败: {str(e)}")


@asynccontextmanager
async def savepoint(session: AsyncSession, name: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
    """
    保存点上下文管理器
    用法:
    async with savepoint(session, "my_savepoint") as sp:
        await sp.execute(...)

    :param session: 数据库会话
    :param name: 保存点名称
    :return: 数据库会话
    :raises TransactionError: 当保存点操作失败时
    """
    if not session.in_transaction():
        raise TransactionError("保存点必须在事务中创建")

    savepoint = await session.begin_nested()
    try:
        yield session
        await savepoint.commit()
    except Exception as e:
        await savepoint.rollback()
        raise TransactionError(f"保存点操作失败: {str(e)}")


# 创建事务上下文实例
transaction_context = TransactionContext()

# 导出
__all__ = [
    "TransactionManager",
    "TransactionContext",
    "transaction_context",
    "transaction",
    "atomic",
    "savepoint",
    "TransactionState",
    "SavePoint",
]
