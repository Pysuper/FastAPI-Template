import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Set

logger = logging.getLogger(__name__)


@dataclass
class TransactionLock:
    """事务锁"""

    transaction_id: str
    resources: Set[str]  # 资源标识符集合
    acquired_at: datetime
    timeout: int = 30  # 锁超时时间(秒)


class ConcurrencyManager:
    """事务并发控制器"""

    def __init__(self, max_concurrent_transactions: int = 100):
        self.max_concurrent_transactions = max_concurrent_transactions
        self._locks: Dict[str, TransactionLock] = {}  # resource -> lock
        self._transaction_resources: Dict[str, Set[str]] = {}  # transaction_id -> resources
        self._semaphore = asyncio.Semaphore(max_concurrent_transactions)

        # 统计信息
        self._stats = {
            "total_transactions": 0,
            "current_transactions": 0,
            "max_concurrent_reached": 0,
            "lock_timeouts": 0,
            "lock_conflicts": 0,
            "deadlocks_detected": 0,
        }

    def _is_deadlock(self, transaction_id: str, resource: str, visited: Set[str]) -> bool:
        """检测死锁"""
        if resource not in self._locks:
            return False

        lock = self._locks[resource]
        if lock.transaction_id == transaction_id:
            return True

        if lock.transaction_id in visited:
            return False

        visited.add(lock.transaction_id)

        # 检查持有该锁的事务是否在等待其他资源
        for other_resource in self._transaction_resources.get(lock.transaction_id, set()):
            if self._is_deadlock(transaction_id, other_resource, visited):
                return True

        return False

    def _clean_expired_locks(self):
        """清理过期的锁"""
        now = datetime.now()
        expired_resources = []

        for resource, lock in self._locks.items():
            if (now - lock.acquired_at).total_seconds() > lock.timeout:
                expired_resources.append(resource)
                self._stats["lock_timeouts"] += 1

        for resource in expired_resources:
            self._release_resource(resource)

    def _release_resource(self, resource: str):
        """释放资源"""
        if resource in self._locks:
            lock = self._locks[resource]
            if lock.transaction_id in self._transaction_resources:
                self._transaction_resources[lock.transaction_id].remove(resource)
                if not self._transaction_resources[lock.transaction_id]:
                    del self._transaction_resources[lock.transaction_id]
            del self._locks[resource]

    async def acquire(self, transaction_id: str, resources: Set[str], timeout: int = 30) -> bool:
        """获取事务锁

        Args:
            transaction_id: 事务ID
            resources: 需要锁定的资源集合
            timeout: 锁超时时间(秒)

        Returns:
            bool: 是否成功获取所有锁
        """
        try:
            # 清理过期锁
            self._clean_expired_locks()

            # 检查是否超过最大并发数
            if not await self._semaphore.acquire():
                return False

            try:
                # 检查资源冲突
                for resource in resources:
                    if resource in self._locks:
                        current_lock = self._locks[resource]
                        if current_lock.transaction_id != transaction_id:
                            # 检查死锁
                            if self._is_deadlock(transaction_id, resource, {transaction_id}):
                                self._stats["deadlocks_detected"] += 1
                                return False
                            self._stats["lock_conflicts"] += 1
                            return False

                # 获取所有资源的锁
                now = datetime.now()
                for resource in resources:
                    self._locks[resource] = TransactionLock(
                        transaction_id=transaction_id, resources=resources, acquired_at=now, timeout=timeout
                    )

                # 记录事务资源
                self._transaction_resources[transaction_id] = resources

                # 更新统计信息
                self._stats["total_transactions"] += 1
                self._stats["current_transactions"] += 1
                self._stats["max_concurrent_reached"] = max(
                    self._stats["max_concurrent_reached"], self._stats["current_transactions"]
                )

                return True

            except Exception as e:
                logger.error(f"Error acquiring locks: {e}")
                self._semaphore.release()
                return False

        except Exception as e:
            logger.error(f"Error in acquire: {e}")
            return False

    async def release(self, transaction_id: str):
        """释放事务锁"""
        try:
            # 释放该事务持有的所有资源
            if transaction_id in self._transaction_resources:
                resources = self._transaction_resources[transaction_id]
                for resource in resources:
                    self._release_resource(resource)

                # 更新统计信息
                self._stats["current_transactions"] -= 1

            # 释放信号量
            self._semaphore.release()

        except Exception as e:
            logger.error(f"Error releasing locks: {e}")

    def get_metrics(self) -> Dict:
        """获取并发控制指标"""
        return {
            "config": {
                "max_concurrent_transactions": self.max_concurrent_transactions,
            },
            "current_state": {
                "active_locks": len(self._locks),
                "active_transactions": len(self._transaction_resources),
            },
            "stats": self._stats.copy(),
        }
