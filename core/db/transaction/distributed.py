import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TransactionState(Enum):
    """事务状态"""

    INIT = "init"  # 初始状态
    PREPARING = "preparing"  # 准备阶段
    PREPARED = "prepared"  # 准备完成
    COMMITTING = "committing"  # 提交阶段
    COMMITTED = "committed"  # 提交完成
    ROLLING_BACK = "rolling_back"  # 回滚阶段
    ROLLED_BACK = "rolled_back"  # 回滚完成
    FAILED = "failed"  # 失败状态


class TransactionParticipant:
    """事务参与者"""

    def __init__(self, name: str, session: AsyncSession, timeout: int = 10):
        self.name = name
        self.session = session
        self.timeout = timeout
        self.state = TransactionState.INIT
        self.prepared_at: Optional[datetime] = None
        self.committed_at: Optional[datetime] = None
        self.rolled_back_at: Optional[datetime] = None
        self.error: Optional[Exception] = None

    async def prepare(self) -> bool:
        """准备阶段"""
        try:
            self.state = TransactionState.PREPARING
            # 开启事务
            await self.session.begin()
            self.state = TransactionState.PREPARED
            self.prepared_at = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Prepare failed for participant {self.name}: {e}")
            self.state = TransactionState.FAILED
            self.error = e
            return False

    async def commit(self) -> bool:
        """提交阶段"""
        try:
            self.state = TransactionState.COMMITTING
            await self.session.commit()
            self.state = TransactionState.COMMITTED
            self.committed_at = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Commit failed for participant {self.name}: {e}")
            self.state = TransactionState.FAILED
            self.error = e
            return False

    async def rollback(self) -> bool:
        """回滚阶段"""
        try:
            self.state = TransactionState.ROLLING_BACK
            await self.session.rollback()
            self.state = TransactionState.ROLLED_BACK
            self.rolled_back_at = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Rollback failed for participant {self.name}: {e}")
            self.state = TransactionState.FAILED
            self.error = e
            return False

    def get_state(self) -> Dict:
        """获取状态信息"""
        return {
            "name": self.name,
            "state": self.state.value,
            "prepared_at": self.prepared_at.isoformat() if self.prepared_at else None,
            "committed_at": self.committed_at.isoformat() if self.committed_at else None,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "error": str(self.error) if self.error else None,
        }


class DistributedTransaction:
    """分布式事务"""

    def __init__(self, transaction_id: str, coordinator_timeout: int = 30, participant_timeout: int = 10):
        self.transaction_id = transaction_id
        self.coordinator_timeout = coordinator_timeout
        self.participant_timeout = participant_timeout
        self.participants: List[TransactionParticipant] = []
        self.state = TransactionState.INIT
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.error: Optional[Exception] = None

    def add_participant(self, name: str, session: AsyncSession) -> TransactionParticipant:
        """添加参与者"""
        participant = TransactionParticipant(name=name, session=session, timeout=self.participant_timeout)
        self.participants.append(participant)
        return participant

    async def prepare(self) -> bool:
        """准备阶段"""
        self.state = TransactionState.PREPARING

        # 并行执行所有参与者的准备操作
        prepare_tasks = [participant.prepare() for participant in self.participants]

        try:
            results = await asyncio.gather(*prepare_tasks)
            success = all(results)

            if success:
                self.state = TransactionState.PREPARED
            else:
                self.state = TransactionState.FAILED
                await self.rollback()

            return success
        except Exception as e:
            logger.error(f"Prepare phase failed: {e}")
            self.state = TransactionState.FAILED
            self.error = e
            await self.rollback()
            return False

    async def commit(self) -> bool:
        """提交阶段"""
        if self.state != TransactionState.PREPARED:
            logger.error("Cannot commit: transaction not prepared")
            return False

        self.state = TransactionState.COMMITTING

        # 并行执行所有参与者的提交操作
        commit_tasks = [participant.commit() for participant in self.participants]

        try:
            results = await asyncio.gather(*commit_tasks)
            success = all(results)

            if success:
                self.state = TransactionState.COMMITTED
            else:
                self.state = TransactionState.FAILED
                await self.rollback()

            self.completed_at = datetime.now()
            return success
        except Exception as e:
            logger.error(f"Commit phase failed: {e}")
            self.state = TransactionState.FAILED
            self.error = e
            await self.rollback()
            return False

    async def rollback(self) -> bool:
        """回滚阶段"""
        self.state = TransactionState.ROLLING_BACK

        # 并行���行所有参与者的回滚操作
        rollback_tasks = [participant.rollback() for participant in self.participants]

        try:
            results = await asyncio.gather(*rollback_tasks)
            success = all(results)

            if success:
                self.state = TransactionState.ROLLED_BACK
            else:
                self.state = TransactionState.FAILED

            self.completed_at = datetime.now()
            return success
        except Exception as e:
            logger.error(f"Rollback phase failed: {e}")
            self.state = TransactionState.FAILED
            self.error = e
            return False

    def get_state(self) -> Dict:
        """获取事务状态"""
        return {
            "transaction_id": self.transaction_id,
            "state": self.state.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": str(self.error) if self.error else None,
            "participants": [p.get_state() for p in self.participants],
        }


class DistributedTransactionManager:
    """分布式事务管理器"""

    def __init__(self, coordinator_timeout: int = 30, participant_timeout: int = 10):
        self.coordinator_timeout = coordinator_timeout
        self.participant_timeout = participant_timeout
        self.active_transactions: Dict[str, DistributedTransaction] = {}
        self._transaction_id = 0

    def _generate_transaction_id(self) -> str:
        """生成事务ID"""
        self._transaction_id += 1
        return f"tx_{self._transaction_id}"

    def create_transaction(self) -> DistributedTransaction:
        """创建新事务"""
        transaction_id = self._generate_transaction_id()
        transaction = DistributedTransaction(
            transaction_id=transaction_id,
            coordinator_timeout=self.coordinator_timeout,
            participant_timeout=self.participant_timeout,
        )
        self.active_transactions[transaction_id] = transaction
        return transaction

    def get_transaction(self, transaction_id: str) -> Optional[DistributedTransaction]:
        """获取事务"""
        return self.active_transactions.get(transaction_id)

    def remove_transaction(self, transaction_id: str):
        """移除事务"""
        if transaction_id in self.active_transactions:
            del self.active_transactions[transaction_id]

    @asynccontextmanager
    async def transaction(self) -> DistributedTransaction:
        """事务上下文管理器"""
        transaction = self.create_transaction()
        try:
            yield transaction
            # 如果没有异常发生,执行提交
            if transaction.state == TransactionState.INIT:
                if await transaction.prepare():
                    await transaction.commit()
        except Exception as e:
            # 发生异常时回滚
            logger.error(f"Transaction failed: {e}")
            await transaction.rollback()
            raise
        finally:
            # 清理事务
            self.remove_transaction(transaction.transaction_id)

    def get_metrics(self) -> Dict:
        """获取管理器指标"""
        return {
            "active_transactions": len(self.active_transactions),
            "coordinator_timeout": self.coordinator_timeout,
            "participant_timeout": self.participant_timeout,
            "transactions": [tx.get_state() for tx in self.active_transactions.values()],
        }
