import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Set

from core.db.transaction.distributed import DistributedTransaction, DistributedTransactionManager, TransactionState

logger = logging.getLogger(__name__)


class TransactionCoordinator:
    """事务协调器"""

    def __init__(
        self,
        manager: DistributedTransactionManager,
        prepare_timeout: int = 10,
        commit_timeout: int = 10,
        rollback_timeout: int = 10,
        retry_interval: int = 1,
        max_retries: int = 3,
    ):
        self.manager = manager
        self.prepare_timeout = prepare_timeout
        self.commit_timeout = commit_timeout
        self.rollback_timeout = rollback_timeout
        self.retry_interval = retry_interval
        self.max_retries = max_retries

    async def _execute_with_retry(self, operation, timeout: int, error_message: str) -> bool:
        """执行带重试的操作"""
        for retry in range(self.max_retries):
            try:
                async with asyncio.timeout(timeout):
                    return await operation()
            except asyncio.TimeoutError:
                logger.error(f"{error_message} timed out after {timeout}s " f"(retry {retry + 1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"{error_message} failed: {e} " f"(retry {retry + 1}/{self.max_retries})")

            if retry < self.max_retries - 1:
                await asyncio.sleep(self.retry_interval)

        return False

    async def prepare(self, transaction: DistributedTransaction) -> bool:
        """准备阶段"""
        return await self._execute_with_retry(
            operation=transaction.prepare,
            timeout=self.prepare_timeout,
            error_message=f"Prepare phase for transaction {transaction.transaction_id}",
        )

    async def commit(self, transaction: DistributedTransaction) -> bool:
        """提交阶段"""
        return await self._execute_with_retry(
            operation=transaction.commit,
            timeout=self.commit_timeout,
            error_message=f"Commit phase for transaction {transaction.transaction_id}",
        )

    async def rollback(self, transaction: DistributedTransaction) -> bool:
        """回滚阶段"""
        return await self._execute_with_retry(
            operation=transaction.rollback,
            timeout=self.rollback_timeout,
            error_message=f"Rollback phase for transaction {transaction.transaction_id}",
        )

    @asynccontextmanager
    async def transaction(self) -> DistributedTransaction:
        """事务上下文管理器"""
        transaction = self.manager.create_transaction()
        try:
            yield transaction

            # 如果没有异常发生,执行两阶段提交
            if transaction.state == TransactionState.INIT:
                # 准备阶段
                if await self.prepare(transaction):
                    # 提交阶段
                    await self.commit(transaction)
                else:
                    # 准备失败,执行回滚
                    await self.rollback(transaction)
        except Exception as e:
            # 发生异常时回滚
            logger.error(f"Transaction {transaction.transaction_id} failed: {e}")
            await self.rollback(transaction)
            raise
        finally:
            # 清理事务
            self.manager.remove_transaction(transaction.transaction_id)

    def get_metrics(self) -> Dict:
        """获取协调器指标"""
        return {
            "prepare_timeout": self.prepare_timeout,
            "commit_timeout": self.commit_timeout,
            "rollback_timeout": self.rollback_timeout,
            "retry_interval": self.retry_interval,
            "max_retries": self.max_retries,
            "manager": self.manager.get_metrics(),
        }


class TransactionRegistry:
    """事务注册表"""

    def __init__(self):
        self.transactions: Dict[str, DistributedTransaction] = {}
        self.participants: Dict[str, Set[str]] = {}  # transaction_id -> participant_names

    def register_transaction(self, transaction: DistributedTransaction):
        """注册事务"""
        self.transactions[transaction.transaction_id] = transaction
        self.participants[transaction.transaction_id] = {p.name for p in transaction.participants}

    def unregister_transaction(self, transaction_id: str):
        """注销事务"""
        if transaction_id in self.transactions:
            del self.transactions[transaction_id]
        if transaction_id in self.participants:
            del self.participants[transaction_id]

    def get_transaction(self, transaction_id: str) -> Optional[DistributedTransaction]:
        """获取事务"""
        return self.transactions.get(transaction_id)

    def get_participant_transactions(self, participant_name: str) -> List[DistributedTransaction]:
        """获取参与者相关的事务"""
        return [tx for tx in self.transactions.values() if participant_name in self.participants[tx.transaction_id]]

    def get_metrics(self) -> Dict:
        """获取注册表指标"""
        return {
            "active_transactions": len(self.transactions),
            "transactions": [
                {"transaction_id": tx_id, "participants": list(participants)}
                for tx_id, participants in self.participants.items()
            ],
        }
