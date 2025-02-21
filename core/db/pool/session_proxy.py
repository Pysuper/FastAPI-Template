import logging
from typing import Any, Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ClauseElement

from core.db.pool.transaction_router import TransactionRouter

logger = logging.getLogger(__name__)


class SessionProxy:
    """会话代理"""

    def __init__(
        self,
        router: TransactionRouter,
        master_session: AsyncSession,
        replica_session: Optional[AsyncSession] = None,
        sticky_master: bool = True,  # 是否开启主库粘性会话
        track_queries: bool = True,  # 是否跟踪查询
    ):
        self.router = router
        self.master_session = master_session
        self.replica_session = replica_session
        self.sticky_master = sticky_master
        self.track_queries = track_queries

        self._in_transaction = False
        self._used_master = False  # 是否使用过主库
        self._query_stats = {
            "total_queries": 0,
            "read_queries": 0,
            "write_queries": 0,
            "master_queries": 0,
            "replica_queries": 0,
        }

    @property
    def active_session(self) -> AsyncSession:
        """获取当前活动会话"""
        # 如果在事务中，使用主库会话
        if self._in_transaction:
            return self.master_session

        # 如果开启主库粘性会话且使用过主库，继续使用主库
        if self.sticky_master and self._used_master:
            return self.master_session

        # 如果没有从库会话，使用主库会话
        if self.replica_session is None:
            return self.master_session

        return self.replica_session

    async def execute(self, statement: ClauseElement, *args, **kwargs) -> Any:
        """执行SQL语句"""
        # 更新查询统计
        if self.track_queries:
            self._query_stats["total_queries"] += 1

        # 判断是否为写操作
        is_write = self.router.is_write_statement(statement)

        if self.track_queries:
            if is_write:
                self._query_stats["write_queries"] += 1
            else:
                self._query_stats["read_queries"] += 1

        # 获取合适的会话
        session = self.master_session if is_write else self.active_session

        # 更新会话使用统计
        if self.track_queries:
            if session is self.master_session:
                self._query_stats["master_queries"] += 1
            else:
                self._query_stats["replica_queries"] += 1

        # 标记使用过主库
        if session is self.master_session:
            self._used_master = True

        # 执行查询
        return await session.execute(statement, *args, **kwargs)

    async def execute_sql(self, sql: str, *args, **kwargs) -> Any:
        """执行原始SQL"""
        # 更新查询统计
        if self.track_queries:
            self._query_stats["total_queries"] += 1

        # 判断是否为写操作
        is_write = self.router.is_write_operation(sql)

        if self.track_queries:
            if is_write:
                self._query_stats["write_queries"] += 1
            else:
                self._query_stats["read_queries"] += 1

        # 获取合适的会话
        session = self.master_session if is_write else self.active_session

        # 更新会话使用统计
        if self.track_queries:
            if session is self.master_session:
                self._query_stats["master_queries"] += 1
            else:
                self._query_stats["replica_queries"] += 1

        # 标记使用过主库
        if session is self.master_session:
            self._used_master = True

        # 执行查询
        return await session.execute(sql, *args, **kwargs)

    async def begin(self):
        """开启事务"""
        self._in_transaction = True
        await self.master_session.begin()

    async def commit(self):
        """提交事务"""
        await self.master_session.commit()
        self._in_transaction = False

    async def rollback(self):
        """回滚事务"""
        await self.master_session.rollback()
        self._in_transaction = False

    async def close(self):
        """关闭会话"""
        await self.master_session.close()
        if self.replica_session:
            await self.replica_session.close()

    def get_stats(self) -> Dict:
        """获取会话统计信息"""
        return {
            "query_stats": self._query_stats,
            "in_transaction": self._in_transaction,
            "used_master": self._used_master,
            "sticky_master": self.sticky_master,
            "track_queries": self.track_queries,
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if exc_type is not None:
            await self.rollback()
        await self.close()
