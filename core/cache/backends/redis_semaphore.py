"""Redis-based distributed semaphore implementation"""

import asyncio
import time
import uuid

from ..base.interface import DistributedSemaphore


class RedisSemaphore(DistributedSemaphore):
    """基于Redis的分布式信号量实现"""

    def __init__(
        self,
        redis_client,
        name: str,
        count: int = 1,
        timeout: int = None,
        retry_interval: float = 0.1,
        expire: int = 30,
    ):
        """
        初始化Redis信号量

        Args:
            redis_client: Redis客户端实例
            name: 信号量名称
            count: 信号量计数器初始值
            timeout: 获取信号量的超时时间
            retry_interval: 重试间隔
            expire: 信号量的过期时间
        """
        self.redis = redis_client
        self.name = f"semaphore:{name}"
        self.count = count
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.expire = expire
        self._owner = str(uuid.uuid4())

    async def acquire(self) -> bool:
        """
        获取信号量

        Returns:
            bool: 是否成功获取信号量
        """
        start_time = time.time()

        while True:
            # 使用Lua脚本保证原子性
            lua_script = """
            local semaphore = KEYS[1]
            local owner = ARGV[1]
            local count = tonumber(ARGV[2])
            local expire = tonumber(ARGV[3])
            
            local current = tonumber(redis.call('get', semaphore) or count)
            if current > 0 then
                redis.call('decr', semaphore)
                redis.call('sadd', semaphore .. ':owners', owner)
                redis.call('expire', semaphore, expire)
                redis.call('expire', semaphore .. ':owners', expire)
                return 1
            end
            return 0
            """

            success = await self.redis.eval(
                lua_script,
                keys=[self.name],
                args=[self._owner, self.count, self.expire],
            )

            if success:
                return True

            if self.timeout is not None:
                if time.time() - start_time >= self.timeout:
                    return False

            await asyncio.sleep(self.retry_interval)

    async def release(self) -> None:
        """释放信号量"""
        lua_script = """
        local semaphore = KEYS[1]
        local owner = ARGV[1]
        local count = tonumber(ARGV[2])
        
        if redis.call('sismember', semaphore .. ':owners', owner) == 1 then
            redis.call('srem', semaphore .. ':owners', owner)
            local current = tonumber(redis.call('get', semaphore) or 0)
            if current < count then
                redis.call('incr', semaphore)
            end
            return 1
        end
        return 0
        """

        await self.redis.eval(lua_script, keys=[self.name], args=[self._owner, self.count])

    async def get_value(self) -> int:
        """
        获取当前信号量的值

        Returns:
            int: 当前信号量值
        """
        value = await self.redis.get(self.name)
        return int(value) if value is not None else self.count

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.release()
