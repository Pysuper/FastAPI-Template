"""
分布式锁管理器
实现基于Redis的分布式锁
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from core.strong.metrics import metrics_collector

logger = logging.getLogger(__name__)


class LockError(Exception):
    """锁错误"""

    pass


class Lock:
    """分布式锁"""

    def __init__(
        self,
        name: str,
        timeout: int = 30,
        blocking: bool = True,
        blocking_timeout: Optional[int] = None,
        lock_id: Optional[str] = None,
    ):
        """
        初始化
        :param name: 锁名称
        :param timeout: 锁超时时间(秒)
        :param blocking: 是否阻塞等待
        :param blocking_timeout: 阻塞超时时间(秒)
        :param lock_id: 锁ID(用于重入)
        """
        self.name = f"lock:{name}"
        self.timeout = timeout
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self.lock_id = lock_id or str(uuid.uuid4())
        self._redis = redis_cache
        self._local = asyncio.Lock()
        self._reentrant_count = 0

    async def acquire(self) -> bool:
        """
        获取锁
        :return: 是否获取成功
        """
        start_time = time.time()

        # 检查是否已经持有锁(重入)
        async with self._local:
            if self._reentrant_count > 0:
                self._reentrant_count += 1
                return True

        while True:
            # 尝试获取锁
            if await self._acquire_lock():
                async with self._local:
                    self._reentrant_count = 1
                return True

            if not self.blocking:
                return False

            # 检查阻塞超时
            if self.blocking_timeout is not None:
                if time.time() - start_time >= self.blocking_timeout:
                    return False

            # 等待一段时间后重试
            await asyncio.sleep(0.1)

    async def _acquire_lock(self) -> bool:
        """
        获取Redis锁
        :return: 是否获取成功
        """
        # 使用SET NX实现锁
        success = await self._redis.set(self.name, self.lock_id, ex=self.timeout, nx=True)

        if success:
            metrics_collector.increment("distributed_locks_acquired_total", 1, {"lock_name": self.name})

        return bool(success)

    async def release(self) -> None:
        """释放锁"""
        async with self._local:
            self._reentrant_count -= 1
            if self._reentrant_count > 0:
                return

        # 使用Lua脚本保证原子性
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """

        result = await self._redis.eval(script, keys=[self.name], args=[self.lock_id])

        if result:
            metrics_collector.increment("distributed_locks_released_total", 1, {"lock_name": self.name})
        else:
            logger.warning(f"Failed to release lock: {self.name}")

    async def extend(self, additional_time: int) -> bool:
        """
        延长锁的过期时间
        :param additional_time: 增加的时间(秒)
        :return: 是否成功
        """
        # 使用Lua脚本保证原子性
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('expire', KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        success = await self._redis.eval(script, keys=[self.name], args=[self.lock_id, additional_time])

        if success:
            metrics_collector.increment("distributed_locks_extended_total", 1, {"lock_name": self.name})

        return bool(success)

    async def reacquire(self) -> bool:
        """
        重新获取锁(用于续约)
        :return: 是否成功
        """
        success = await self._redis.set(self.name, self.lock_id, ex=self.timeout, xx=True)

        if success:
            metrics_collector.increment("distributed_locks_reacquired_total", 1, {"lock_name": self.name})

        return bool(success)


class LockManager:
    """分布式锁管理器"""

    def __init__(self):
        self._redis = redis_cache
        self._active_locks: dict = {}

    @asynccontextmanager
    async def lock(self, name: str, timeout: int = 30, blocking: bool = True, blocking_timeout: Optional[int] = None):
        """
        获取锁的上下文管理器
        :param name: 锁名称
        :param timeout: 锁超时时间(秒)
        :param blocking: 是否阻塞等待
        :param blocking_timeout: 阻塞超时时间(秒)
        """
        lock = Lock(name, timeout, blocking, blocking_timeout)

        try:
            if not await lock.acquire():
                raise LockError(f"Failed to acquire lock: {name}")

            self._active_locks[name] = lock
            yield lock

        finally:
            await lock.release()
            self._active_locks.pop(name, None)

    async def force_release_all(self) -> None:
        """强制释放所有锁"""
        for name, lock in list(self._active_locks.items()):
            try:
                await lock.release()
            except Exception as e:
                logger.error(f"Error releasing lock {name}: {e}")
            self._active_locks.pop(name, None)

    async def get_active_locks(self) -> list:
        """获取当前活动的锁"""
        return list(self._active_locks.keys())

    async def is_locked(self, name: str) -> bool:
        """
        检查锁是否被占用
        :param name: 锁名称
        :return: 是否被占用
        """
        return await self._redis.exists(f"lock:{name}")


# 创建默认锁管理器实例
lock_manager = LockManager()

# 导出
__all__ = ["lock_manager", "LockManager", "Lock", "LockError"]
