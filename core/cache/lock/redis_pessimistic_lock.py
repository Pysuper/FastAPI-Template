"""
Redis-based pessimistic lock implementation
"""

import asyncio
import time
import uuid
from typing import Optional

from core.cache.base.interface import PessimisticLock


class RedisPessimisticLock(PessimisticLock):
    """
    基于Redis的悲观锁实现
    """

    def __init__(
        self,
        redis_client,
        name: str,
        timeout: Optional[int] = None,
        retry_interval: float = 0.1,
        expire: int = 30,
    ):
        """
        初始化悲观锁

        Args:
            redis_client: Redis客户端实例
            name: 锁名称
            timeout: 获取锁的超时时间
            retry_interval: 重试间隔
            expire: 锁的过期时间
        """
        self.redis = redis_client
        self.name = f"pessimistic_lock:{name}"
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.expire = expire
        self._owner = str(uuid.uuid4())
        self._lock_time = None

    async def acquire(self) -> bool:
        """获取锁"""
        return await self.acquire_with_timeout(self.timeout)

    async def acquire_with_timeout(self, timeout: Optional[int] = None) -> bool:
        """
        带超时的锁获取

        Args:
            timeout: 获取锁的超时时间（秒）

        Returns:
            bool: 是否成功获取锁
        """
        start_time = time.time()
        timeout = timeout or self.timeout

        while True:
            success = await self._try_acquire()
            if success:
                self._lock_time = time.time()
                return True

            if timeout is not None:
                if time.time() - start_time >= timeout:
                    return False

            await asyncio.sleep(self.retry_interval)

    async def _try_acquire(self) -> bool:
        """
        尝试获取锁

        Returns:
            bool: 是否成功获取锁
        """
        lua_script = """
        local lock_key = KEYS[1]
        local owner = ARGV[1]
        local expire = tonumber(ARGV[2])
        
        if redis.call('exists', lock_key) == 0 then
            redis.call('set', lock_key, owner)
            redis.call('expire', lock_key, expire)
            return 1
        end
        return 0
        """

        return bool(await self.redis.eval(lua_script, keys=[self.name], args=[self._owner, self.expire]))

    async def release(self) -> None:
        """释放锁"""
        lua_script = """
        local lock_key = KEYS[1]
        local owner = ARGV[1]
        
        if redis.call('get', lock_key) == owner then
            return redis.call('del', lock_key)
        end
        return 0
        """

        await self.redis.eval(lua_script, keys=[self.name], args=[self._owner])
        self._lock_time = None

    async def force_unlock(self) -> bool:
        """
        强制解锁

        Returns:
            bool: 是否成功解锁
        """
        return bool(await self.redis.delete(self.name))

    async def get_hold_time(self) -> Optional[float]:
        """
        获取锁的持有时间

        Returns:
            Optional[float]: 持有时间（秒），如果未持有锁则返回None
        """
        if self._lock_time is None:
            return None
        return time.time() - self._lock_time

    async def is_locked(self) -> bool:
        """
        检查锁是否被持有

        Returns:
            bool: 锁是否被持有
        """
        return await self.redis.exists(self.name)

    async def extend(self, additional_time: int) -> bool:
        """
        延长锁的过期时间

        Args:
            additional_time: 要增加的时间（秒）

        Returns:
            bool: 是否成功延长
        """
        lua_script = """
        local lock_key = KEYS[1]
        local owner = ARGV[1]
        local additional_time = tonumber(ARGV[2])
        
        if redis.call('get', lock_key) == owner then
            return redis.call('expire', lock_key, additional_time)
        end
        return 0
        """

        return bool(
            await self.redis.eval(
                lua_script,
                keys=[self.name],
                args=[self._owner, additional_time],
            )
        )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.release()
