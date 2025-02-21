"""
重试机制模块
"""
import asyncio
import logging
from functools import wraps
from typing import Type, Tuple, Optional, Callable, Any

from cache.exceptions import CacheError, CacheConnectionError, CacheTimeoutError

logger = logging.getLogger(__name__)


class RetryStrategy:
    """重试策略"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 0.1,
        max_delay: float = 2.0,
        backoff_factor: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (CacheConnectionError, CacheTimeoutError),
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions

    def get_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)


def retryable(
    strategy: Optional[RetryStrategy] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """重试装饰器

    Args:
        strategy: 重试策略
        on_retry: 重试回调函数
    """
    if strategy is None:
        strategy = RetryStrategy()

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, strategy.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except strategy.exceptions as e:
                    last_exception = e

                    if attempt == strategy.max_retries:
                        break

                    if on_retry:
                        on_retry(e, attempt)

                    delay = strategy.get_delay(attempt)
                    logger.warning(
                        f"Retry attempt {attempt}/{strategy.max_retries} " f"for {func.__name__} after {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
                except Exception as e:
                    raise CacheError(f"Unexpected error in {func.__name__}", cause=e)

            raise last_exception

        return wrapper

    return decorator


class RetryableCache:
    """带重试的缓存包装器"""

    def __init__(self, cache: Any, strategy: Optional[RetryStrategy] = None):
        self.cache = cache
        self.strategy = strategy or RetryStrategy()

        # 包装所有公共方法
        for name in dir(cache):
            if not name.startswith("_"):
                attr = getattr(cache, name)
                if callable(attr):
                    setattr(self, name, retryable(strategy=self.strategy)(attr))
