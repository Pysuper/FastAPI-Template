import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """限流配置"""

    max_requests: int = 1000  # 最大请求数
    time_window: int = 60  # 时间窗口(秒)
    max_concurrent: int = 100  # 最大并发数
    max_wait_time: int = 10  # 最大等待时间(秒)


class RateLimiter:
    """连接池限流器"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._requests = []  # 请求时间列表
        self._semaphore = asyncio.Semaphore(config.max_concurrent)
        self._stats = {
            "total_requests": 0,
            "rejected_requests": 0,
            "queued_requests": 0,
            "current_concurrent": 0,
            "max_concurrent_reached": 0,
            "total_wait_time": 0.0,
        }

    def _clean_old_requests(self):
        """清理过期请求"""
        now = time.time()
        window_start = now - self.config.time_window
        self._requests = [t for t in self._requests if t > window_start]

    def _check_rate_limit(self) -> bool:
        """检查是否超过速率限制"""
        self._clean_old_requests()
        return len(self._requests) < self.config.max_requests

    async def acquire(self) -> bool:
        """获取执行许可

        Returns:
            bool: 是否获取到许可
        """
        try:
            # 检查速率限制
            if not self._check_rate_limit():
                self._stats["rejected_requests"] += 1
                return False

            # 记录请求
            self._requests.append(time.time())
            self._stats["total_requests"] += 1

            # 尝试获取信号量
            start_time = time.time()
            try:
                async with asyncio.timeout(self.config.max_wait_time):
                    self._stats["queued_requests"] += 1
                    await self._semaphore.acquire()
                    wait_time = time.time() - start_time
                    self._stats["total_wait_time"] += wait_time
            except asyncio.TimeoutError:
                self._stats["rejected_requests"] += 1
                return False

            # 更新并发统计
            self._stats["current_concurrent"] += 1
            self._stats["max_concurrent_reached"] = max(
                self._stats["max_concurrent_reached"], self._stats["current_concurrent"]
            )

            return True
        except Exception as e:
            logger.error(f"Error acquiring rate limit: {e}")
            return False

    async def release(self):
        """释放执行许可"""
        try:
            self._semaphore.release()
            self._stats["current_concurrent"] -= 1
        except Exception as e:
            logger.error(f"Error releasing rate limit: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        success = await self.acquire()
        if not success:
            raise asyncio.TimeoutError("Rate limit exceeded")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.release()

    def get_metrics(self) -> Dict:
        """获取限流器指标"""
        self._clean_old_requests()

        current_rate = len(self._requests) / self.config.time_window
        avg_wait_time = (
            self._stats["total_wait_time"] / self._stats["total_requests"] if self._stats["total_requests"] > 0 else 0.0
        )

        return {
            "config": {
                "max_requests": self.config.max_requests,
                "time_window": self.config.time_window,
                "max_concurrent": self.config.max_concurrent,
                "max_wait_time": self.config.max_wait_time,
            },
            "current_state": {
                "current_requests": len(self._requests),
                "current_rate": current_rate,
                "current_concurrent": self._stats["current_concurrent"],
            },
            "stats": {
                **self._stats,
                "avg_wait_time": avg_wait_time,
            },
        }
