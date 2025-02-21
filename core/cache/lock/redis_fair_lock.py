"""
Redis-based fair lock implementation
"""

import asyncio
import time
import uuid
from typing import Optional

from core.cache.base.interface import DistributedLock


class RedisFairLock(DistributedLock):
    """基于Redis的公平锁实现"""

    def __init__(
        self,
        redis_client,
        name: str,
        timeout: int = None,
        retry_interval: float = 0.1,
        expire: int = 30,
    ):
        """
        初始化公平锁

        Args:
            redis_client: Redis客户端实例
            name: 锁名称
            timeout: 获取锁的超时时间
            retry_interval: 重试间隔
            expire: 锁的过期时间
        """
        self.redis = redis_client
        self.name = f"fair_lock:{name}"
        self.queue_key = f"{self.name}:queue"
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.expire = expire
        self._owner = str(uuid.uuid4())

    async def acquire(self) -> bool:
        """
        获取公平锁

        Returns:
            bool: 是否成功获取锁
        """
        start_time = time.time()

        # 将当前请求加入等待队列
        await self.redis.rpush(self.queue_key, self._owner)
        await self.redis.expire(self.queue_key, self.expire)

        try:
            while True:
                # 检查是否是队列头部的请求
                lua_script = """
                local lock_key = KEYS[1]
                local queue_key = KEYS[2]
                local owner = ARGV[1]
                local expire = tonumber(ARGV[2])
                
                -- 检查队列头部是否是当前请求
                local head = redis.call('lindex', queue_key, 0)
                if head == owner then
                    -- 尝试获取锁
                    if redis.call('set', lock_key, owner, 'NX', 'EX', expire) then
                        -- 成功获取锁后从队列中移除
                        redis.call('lpop', queue_key)
                        return 1
                    end
                end
                return 0
                """

                success = await self.redis.eval(
                    lua_script,
                    keys=[self.name, self.queue_key],
                    args=[self._owner, self.expire],
                )

                if success:
                    return True

                if self.timeout is not None:
                    if time.time() - start_time >= self.timeout:
                        # 超时后从队列中移除
                        await self._remove_from_queue()
                        return False

                await asyncio.sleep(self.retry_interval)

        except Exception:
            # 发生异常时确保从队列中移除
            await self._remove_from_queue()
            raise

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

    async def _remove_from_queue(self) -> None:
        """从等待队列中移除当前请求"""
        lua_script = """
        local queue_key = KEYS[1]
        local owner = ARGV[1]
        
        local index = 0
        while true do
            local value = redis.call('lindex', queue_key, index)
            if not value then
                break
            end
            if value == owner then
                redis.call('lrem', queue_key, 1, owner)
                break
            end
            index = index + 1
        end
        """

        await self.redis.eval(lua_script, keys=[self.queue_key], args=[self._owner])

    async def get_queue_length(self) -> int:
        """
        获取等待队列长度

        Returns:
            int: 等待队列长度
        """
        return await self.redis.llen(self.queue_key)

    async def get_queue_position(self) -> Optional[int]:
        """
        获取当前请求在队列中的位置

        Returns:
            Optional[int]: 队列位置（从0开始），如果不在队列中则返回None
        """
        queue = await self.redis.lrange(self.queue_key, 0, -1)
        try:
            return queue.index(self._owner)
        except ValueError:
            return None

    async def is_locked(self) -> bool:
        """
        检查锁是否被持有

        Returns:
            bool: 锁是否被持有
        """
        return bool(await self.redis.exists(self.name))

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.release()
