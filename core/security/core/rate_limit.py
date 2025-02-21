"""
请求频率限制中间件
实现基于滑动窗口的限流机制
"""

import time
from typing import Tuple

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.config.setting import settings
from core.config.manager import config_manager


class RateLimiter:
    """
    滑动窗口限流器
    """

    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # 窗口大小(秒)
        self.max_requests = max_requests  # 最大请求数
        self._cache = {}  # 本地缓存

    def _cleanup_old_requests(self, now: float) -> None:
        """清理过期的请求记录"""
        cutoff = now - self.window_size
        for key in list(self._cache.keys()):
            requests = self._cache[key]
            valid_requests = [ts for ts in requests if ts > cutoff]
            if valid_requests:
                self._cache[key] = valid_requests
            else:
                del self._cache[key]

    def is_allowed(self, key: str) -> bool:
        """
        检查请求是否允许
        :param key: 限流键
        :return: 是否允许请求
        """
        now = time.time()
        self._cleanup_old_requests(now)

        if key not in self._cache:
            self._cache[key] = []

        requests = self._cache[key]
        if len(requests) < self.max_requests:
            requests.append(now)
            return True

        return False

    async def init(self):
        pass

    async def close(self):
        pass

    async def reload(self, config):
        pass


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求频率限制中间件
    支持IP限流和用户限流
    """

    def __init__(self, app):
        super().__init__(app)
        self.config = config_manager.security
        self.cache = settings.cache
        self.rate_limiter = RateLimiter(
            window_size=self.config.RATE_LIMIT_WINDOW,
            max_requests=self.config.RATE_LIMIT_REQUESTS,
        )

    def _get_cache_key(self, request: Request) -> str:
        """
        生成缓存键
        基于IP和用户ID(如果有)
        """
        parts = ["rate_limit"]

        # 添加IP
        if self.config.RATE_LIMIT_BY_IP:
            parts.append(f"ip:{request.client.host}")

        # 添加用户ID
        if self.config.RATE_LIMIT_BY_USER:
            user = getattr(request.state, "user", None)
            if user:
                parts.append(f"user:{user['id']}")

        return ":".join(parts)

    async def _get_rate_limit_data(self, key: str) -> Tuple[int, float]:
        """
        获取限流数据
        :return: (请求次数, 重置时间)
        """
        data = await self.cache.get(key)
        if not data:
            return 0, time.time() + self.config.RATE_LIMIT_WINDOW
        return data["count"], data["reset_at"]

    async def _update_rate_limit_data(self, key: str, count: int, reset_at: float) -> None:
        """更新限流数据"""
        await self.cache.set(
            key,
            {"count": count, "reset_at": reset_at},
            expire=self.config.RATE_LIMIT_WINDOW,
        )

    def _is_path_excluded(self, path: str) -> bool:
        """检查路径是否在排除列表中"""
        return any(path.startswith(excluded_path) for excluded_path in self.config.RATE_LIMIT_EXCLUDE_PATHS)

    async def dispatch(self, request: Request, call_next):
        # 检查是否启用限流
        if not self.config.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # 检查是否排除当前路径
        if self._is_path_excluded(request.url.path):
            return await call_next(request)

        # 获取限流键
        cache_key = self._get_cache_key(request)

        # 检查是否允许请求
        if not self.rate_limiter.is_allowed(cache_key):
            # 计算需要等待的时间
            count, reset_at = await self._get_rate_limit_data(cache_key)
            wait_time = int(reset_at - time.time())
            raise RateLimitExceeded(
                message="请求过于频繁",
                wait_time=wait_time,
                details={
                    "key": cache_key,
                    "max_requests": self.config.RATE_LIMIT_REQUESTS,
                    "window": self.config.RATE_LIMIT_WINDOW
                }
            )

        # 获取当前限流数据
        count, reset_at = await self._get_rate_limit_data(cache_key)

        # 更新计数
        now = time.time()
        if now > reset_at:
            count = 1
            reset_at = now + self.config.RATE_LIMIT_WINDOW
        else:
            count += 1

        # 更新限流数据
        await self._update_rate_limit_data(cache_key, count, reset_at)

        # 添加限流响应头
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.config.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.config.RATE_LIMIT_REQUESTS - count))
        response.headers["X-RateLimit-Reset"] = str(int(reset_at))

        return response
