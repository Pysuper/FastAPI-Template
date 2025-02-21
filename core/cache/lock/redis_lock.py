"""
Redis分布式锁实现
"""

import asyncio
import time
import uuid
from datetime import timedelta
from typing import Optional, Union

from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.cache.base.interface import DistributedLock


class RedisLock(DistributedLock):
    """
    Redis分布式锁实现

    基于Redis的分布式锁实现，使用SET命令的NX和PX选项实现锁机制。
    支持锁超时、自动续期、重入等特性。
    """

    def __init__(
        self,
        redis: Redis,
        name: str,
        expire: int = 30,
        timeout: Optional[float] = None,
        retry_interval: float = 0.1,
        retry_times: int = 3,
        prefix: str = "lock:",
    ):
        """初始化Redis分布式锁

        Args:
            redis: Redis客户端实例
            name: 锁名称
            expire: 锁的过期时间（秒）
            timeout: 获取锁的超时时间（秒），None表示一直等待
            retry_interval: 重试间隔（秒）
            retry_times: 重试次数
            prefix: 锁键前缀
        """
        self._redis = redis
        self._name = name
        self._expire = expire
        self._timeout = timeout
        self._retry_interval = retry_interval
        self._retry_times = retry_times
        self._prefix = prefix

        self._lock_key = f"{self._prefix}{self._name}"
        self._lock_token = str(uuid.uuid4())
        self._locked = False
        self._auto_renewal_task = None

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """获取锁

        Args:
            timeout: 获取锁的超时时间（秒），覆盖初始化时的设置

        Returns:
            bool: 是否成功获取锁
        """
        timeout = timeout if timeout is not None else self._timeout
        retry_until = time.time() + timeout if timeout is not None else None

        while True:
            if await self._acquire_lock():
                return True

            if retry_until is not None and time.time() > retry_until:
                return False

            await asyncio.sleep(self._retry_interval)

    async def release(self) -> bool:
        """释放锁

        Returns:
            bool: 是否成功释放锁
        """
        if not self._locked:
            return False

        # 停止自动续期任务
        if self._auto_renewal_task:
            self._auto_renewal_task.cancel()
            self._auto_renewal_task = None

        # 使用Lua脚本确保原子性操作
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """

        try:
            result = await self._redis.eval(script, keys=[self._lock_key], args=[self._lock_token])
            self._locked = False
            return bool(result)
        except RedisError:
            return False

    async def extend(self, additional_time: Union[int, timedelta]) -> bool:
        """延长锁的过期时间

        Args:
            additional_time: 要增加的时间（秒或timedelta）

        Returns:
            bool: 是否成功延长
        """
        if not self._locked:
            return False

        if isinstance(additional_time, timedelta):
            additional_time = int(additional_time.total_seconds())

        # 使用Lua脚本确保原子性操作
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('pexpire', KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        try:
            result = await self._redis.eval(
                script,
                keys=[self._lock_key],
                args=[self._lock_token, additional_time * 1000],
            )
            return bool(result)
        except RedisError:
            return False

    async def is_locked(self) -> bool:
        """检查锁是否被持有

        Returns:
            bool: 锁是否被持有
        """
        try:
            value = await self._redis.get(self._lock_key)
            return bool(value)
        except RedisError:
            return False

    async def _acquire_lock(self) -> bool:
        """尝试获取锁的内部方法"""
        try:
            success = await self._redis.set(
                self._lock_key,
                self._lock_token,
                nx=True,
                px=int(self._expire * 1000),
            )
            if success:
                self._locked = True
                # 启动自动续期任务
                self._start_auto_renewal()
            return success
        except RedisError:
            return False

    def _start_auto_renewal(self) -> None:
        """启动自动续期任务"""

        async def renew_lock():
            while True:
                # 在过期时间的2/3处续期
                await asyncio.sleep(self._expire * 2 / 3)
                if not self._locked:
                    break
                await self.extend(self._expire)

        self._auto_renewal_task = asyncio.create_task(renew_lock())

    async def __aenter__(self) -> "RedisLock":
        """异步上下文管理器入口"""
        if not await self.acquire():
            raise TimeoutError("Failed to acquire lock")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.release()
