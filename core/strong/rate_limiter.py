"""
请求限流器模块
实现基于Redis的滑动窗口限流算法
"""

import time
from typing import List, Optional, Tuple

from cache.backends.redis_ import redis_cache
from core.security.core.exceptions import RateLimitExceeded


class RateLimiter:
    """基于Redis的滑动窗口限流器"""

    def __init__(
        self,
        window_size: int = 60,
        max_requests: int = 100,
        whitelist: List[str] = None,
        max_failures: int = 5,  # 最大失败次数
        failure_window: int = 300,  # 失败计数窗口(秒)
        failure_ban_time: int = 1800,  # 失败次数过多后的禁止时间(秒)
    ):
        """
        初始化限流器
        :param window_size: 时间窗口大小(秒)
        :param max_requests: 窗口内最大请求数
        :param whitelist: IP白名单列表
        :param max_failures: 最大失败次数
        :param failure_window: 失败计数窗口(秒)
        :param failure_ban_time: 失败禁止时间(秒)
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.whitelist = whitelist or []
        self.max_failures = max_failures
        self.failure_window = failure_window
        self.failure_ban_time = failure_ban_time
        self.redis = redis_cache
        self._initialized = False

    async def _ensure_redis_initialized(self) -> None:
        """确保Redis客户端已初始化"""
        if not self._initialized:
            await self.redis.init()
            self._initialized = True

    async def is_allowed(self, key: str, client_ip: str = None) -> Tuple[bool, Optional[int]]:
        """
        检查请求是否允许通过
        :param key: 限流键(如: IP地址、用户ID等)
        :param client_ip: 客户端IP
        :return: (是否允许, 剩余等待时间)
        """
        await self._ensure_redis_initialized()

        # 检查白名单
        if client_ip and client_ip in self.whitelist:
            return True, None

        # 检查是否被禁止访问
        ban_key = f"{key}:ban"
        if await self.redis._client.exists(ban_key):
            ban_ttl = await self.redis._client.ttl(ban_key)
            return False, ban_ttl

        current = time.time()
        window_start = current - self.window_size

        async with self.redis._client.pipeline(transaction=True) as pipe:
            # 移除窗口外的请求记录
            await pipe.zremrangebyscore(key, 0, window_start)
            # 获取当前窗口内的请求数
            await pipe.zcard(key)
            # 添加当前请求记录
            await pipe.zadd(key, {str(current): current})
            # 设置过期时间
            await pipe.expire(key, self.window_size)
            # 执行命令
            _, current_requests, _, _ = await pipe.execute()

        if current_requests > self.max_requests:
            # 计算需要等待的时间
            oldest_request = await self.redis._client.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                wait_time = int(self.window_size - (current - oldest_request[0][1]))
                return False, max(0, wait_time)
            return False, self.window_size

        return True, None

    async def record_failure(self, key: str, client_ip: str = None) -> None:
        """
        记录失败次数
        :param key: 限流键
        :param client_ip: 客户端IP
        """
        await self._ensure_redis_initialized()

        if client_ip and client_ip in self.whitelist:
            return

        failure_key = f"{key}:failures"
        current = time.time()
        window_start = current - self.failure_window

        async with self.redis._client.pipeline(transaction=True) as pipe:
            # 移除窗口外的失败记录
            await pipe.zremrangebyscore(failure_key, 0, window_start)
            # 添加当前失败记录
            await pipe.zadd(failure_key, {str(current): current})
            # 获取失败次数
            await pipe.zcard(failure_key)
            # 设置过期时间
            await pipe.expire(failure_key, self.failure_window)
            # 执行命令
            _, _, failures, _ = await pipe.execute()

        # 如果失败次数超过限制，设置禁止访问
        if failures >= self.max_failures:
            ban_key = f"{key}:ban"
            await self.redis._client.setex(ban_key, self.failure_ban_time, 1)

    async def record_success(self, key: str) -> None:
        """
        记录成功请求，重置失败计数
        :param key: 限流键
        """
        await self._ensure_redis_initialized()

        failure_key = f"{key}:failures"
        ban_key = f"{key}:ban"
        await self.redis._client.delete(failure_key, ban_key)

    async def acquire(self, key: str, client_ip: str = None) -> None:
        """
        获取访问许可
        :param key: 限流键
        :param client_ip: 客户端IP
        :raises RateLimitExceeded: 超过限流阈值时抛出异常
        """
        await self._ensure_redis_initialized()

        allowed, wait_time = await self.is_allowed(key, client_ip)
        if not allowed:
            raise RateLimitExceeded(
                message="请求过于频繁",
                wait_time=wait_time,
                details={"key": key, "max_requests": self.max_requests, "window_size": self.window_size},
            )

    async def get_remaining(self, key: str) -> Tuple[int, int]:
        """
        获取剩余可用请求数和重置时间
        :param key: 限流键
        :return: (剩余请求数, 重置时间)
        """
        await self._ensure_redis_initialized()

        current = time.time()
        window_start = current - self.window_size

        # 清理过期记录
        await self.redis._client.zremrangebyscore(key, 0, window_start)

        # 获取当前请求数
        current_requests = await self.redis._client.zcard(key)
        remaining = max(0, self.max_requests - current_requests)

        # 获取最早请求时间
        oldest_request = await self.redis._client.zrange(key, 0, 0, withscores=True)
        if oldest_request:
            reset_time = int(oldest_request[0][1] + self.window_size - current)
        else:
            reset_time = 0

        return remaining, reset_time

    async def reset(self, key: str) -> None:
        """
        重置限流计数器
        :param key: 限流键
        """
        await self._ensure_redis_initialized()

        await self.redis._client.delete(key)
        await self.redis._client.delete(f"{key}:failures")
        await self.redis._client.delete(f"{key}:ban")


# 创建默认限流器实例
rate_limiter = RateLimiter()

# 导出
__all__ = ["rate_limiter", "RateLimiter"]
