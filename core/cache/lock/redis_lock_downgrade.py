"""
Redis-based distributed lock with downgrade support
"""

import asyncio
import time
import uuid

from core.cache.base.interface import DistributedLock


class RedisLockDowngrade(DistributedLock):
    """
    支持锁降级的Redis分布式锁实现
    """

    LOCK_TYPES = {"exclusive": 2, "shared": 1, "none": 0}  # 排他锁  # 共享锁  # 无锁

    def __init__(
        self,
        redis_client,
        name: str,
        timeout: int = None,
        retry_interval: float = 0.1,
        expire: int = 30,
    ):
        """
        初始化可降级的Redis锁

        Args:
            redis_client: Redis客户端实例
            name: 锁名称
            timeout: 获取锁的超时时间
            retry_interval: 重试间隔
            expire: 锁的过期时间
        """
        self.redis = redis_client
        self.name = f"lock:{name}"
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.expire = expire
        self._owner = str(uuid.uuid4())
        self._current_lock_type = "none"

    async def acquire_exclusive(self) -> bool:
        """
        获取排他锁

        Returns:
            bool: 是否成功获取锁
        """
        success = await self._acquire_lock("exclusive")
        if success:
            self._current_lock_type = "exclusive"
        return success

    async def acquire_shared(self) -> bool:
        """
        获取共享锁

        Returns:
            bool: 是否成功获取锁
        """
        success = await self._acquire_lock("shared")
        if success:
            self._current_lock_type = "shared"
        return success

    async def downgrade(self) -> bool:
        """
        将排他锁降级为共享锁

        Returns:
            bool: 是否成功降级
        """
        if self._current_lock_type != "exclusive":
            return False

        lua_script = """
        local lock_key = KEYS[1]
        local owner = ARGV[1]
        local expire = tonumber(ARGV[2])
        
        if redis.call('get', lock_key) == owner then
            redis.call('hset', lock_key .. ':shared', owner, 1)
            redis.call('expire', lock_key .. ':shared', expire)
            redis.call('del', lock_key)
            return 1
        end
        return 0
        """

        success = await self.redis.eval(
            lua_script,
            keys=[self.name],
            args=[self._owner, self.expire],
        )

        if success:
            self._current_lock_type = "shared"
            return True
        return False

    async def _acquire_lock(self, lock_type: str) -> bool:
        """
        获取指定类型的锁

        Args:
            lock_type: 锁类型 ('exclusive' 或 'shared')

        Returns:
            bool: 是否成功获取锁
        """
        start_time = time.time()

        while True:
            if lock_type == "exclusive":
                success = await self._try_acquire_exclusive()
            else:
                success = await self._try_acquire_shared()

            if success:
                return True

            if self.timeout is not None:
                if time.time() - start_time >= self.timeout:
                    return False

            await asyncio.sleep(self.retry_interval)

    async def _try_acquire_exclusive(self) -> bool:
        """尝试获取排他锁"""
        return await self.redis.set(self.name, self._owner, ex=self.expire, nx=True)

    async def _try_acquire_shared(self) -> bool:
        """尝试获取共享锁"""
        lua_script = """
        local lock_key = KEYS[1]
        local shared_key = lock_key .. ':shared'
        local owner = ARGV[1]
        local expire = tonumber(ARGV[2])
        
        if redis.call('exists', lock_key) == 0 then
            redis.call('hset', shared_key, owner, 1)
            redis.call('expire', shared_key, expire)
            return 1
        end
        return 0
        """

        return await self.redis.eval(
            lua_script,
            keys=[self.name],
            args=[self._owner, self.expire],
        )

    async def release(self) -> None:
        """释放锁"""
        if self._current_lock_type == "exclusive":
            await self._release_exclusive()
        elif self._current_lock_type == "shared":
            await self._release_shared()

        self._current_lock_type = "none"

    async def _release_exclusive(self) -> None:
        """释放排他锁"""
        lua_script = """
        local lock_key = KEYS[1]
        local owner = ARGV[1]
        
        if redis.call('get', lock_key) == owner then
            return redis.call('del', lock_key)
        end
        return 0
        """

        await self.redis.eval(lua_script, keys=[self.name], args=[self._owner])

    async def _release_shared(self) -> None:
        """释放共享锁"""
        lua_script = """
        local lock_key = KEYS[1]
        local shared_key = lock_key .. ':shared'
        local owner = ARGV[1]
        
        redis.call('hdel', shared_key, owner)
        if redis.call('hlen', shared_key) == 0 then
            redis.call('del', shared_key)
        end
        """

        await self.redis.eval(lua_script, keys=[self.name], args=[self._owner])

    async def is_locked(self) -> bool:
        """
        检查锁是否被持有

        Returns:
            bool: 锁是否被持有
        """
        exclusive_exists = await self.redis.exists(self.name)
        shared_exists = await self.redis.exists(f"{self.name}:shared")
        return bool(exclusive_exists or shared_exists)

    async def get_lock_type(self) -> str:
        """
        获取当前锁的类型

        Returns:
            str: 锁类型 ('exclusive', 'shared' 或 'none')
        """
        return self._current_lock_type

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.acquire_exclusive()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.release()
