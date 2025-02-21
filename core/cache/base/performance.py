"""
性能优化模块
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.cache.base.interface import CacheBackend

logger = logging.getLogger(__name__)


class HotKeyTracker:
    """热点键追踪器"""

    def __init__(
        self,
        window_size: int = 60,  # 时间窗口大小（秒）
        bucket_size: int = 10,  # 时间桶大小（秒）
        threshold: int = 100,  # 热点阈值
    ):
        self.window_size = window_size
        self.bucket_size = bucket_size
        self.threshold = threshold
        self.num_buckets = window_size // bucket_size
        self._buckets: List[Dict[str, int]] = [{} for _ in range(self.num_buckets)]
        self._current_bucket = 0
        self._last_rotation = time.time()

    def record_access(self, key: str):
        """记录键访问"""
        self._rotate_if_needed()
        self._buckets[self._current_bucket][key] = self._buckets[self._current_bucket].get(key, 0) + 1

    def get_hot_keys(self) -> Set[str]:
        """获取热点键"""
        self._rotate_if_needed()

        # 合并所有桶的访问计数
        counts: Dict[str, int] = {}
        for bucket in self._buckets:
            for key, count in bucket.items():
                counts[key] = counts.get(key, 0) + count

        # 返回超过阈值的键
        return {key for key, count in counts.items() if count >= self.threshold}

    def _rotate_if_needed(self):
        """根据需要轮转时间桶"""
        now = time.time()
        elapsed = int(now - self._last_rotation)

        if elapsed >= self.bucket_size:
            rotations = min(elapsed // self.bucket_size, self.num_buckets)

            # 清空过期的桶
            for _ in range(rotations):
                self._current_bucket = (self._current_bucket + 1) % self.num_buckets
                self._buckets[self._current_bucket].clear()

            self._last_rotation = now


class CacheOptimizer:
    """缓存优化器"""

    def __init__(
        self,
        cache: CacheBackend,
        hot_key_window: int = 60,
        hot_key_threshold: int = 100,
        prefetch_threshold: float = 0.8,  # 预取阈值（剩余TTL比例）
    ):
        self.cache = cache
        self.hot_key_tracker = HotKeyTracker(window_size=hot_key_window, threshold=hot_key_threshold)
        self.prefetch_threshold = prefetch_threshold
        self._prefetch_tasks: Dict[str, asyncio.Task] = {}

    async def get(self, key: str) -> Optional[Any]:
        """优化的获取操作"""
        # 记录访问
        self.hot_key_tracker.record_access(key)

        # 获取值
        value = await self.cache.get(key)

        # 检查是否需要预取
        if value is not None:
            await self._check_prefetch(key)

        return value

    async def _check_prefetch(self, key: str):
        """检查是否需要预取"""
        try:
            # 获取TTL
            ttl = await self.cache.ttl(key)
            if ttl is None:
                return

            # 如果剩余TTL低于阈值且是热点键，启动预取
            if (
                ttl.total_seconds() / self.cache.default_expire < self.prefetch_threshold
                and key in self.hot_key_tracker.get_hot_keys()
                and key not in self._prefetch_tasks
            ):
                self._start_prefetch(key)
        except Exception as e:
            logger.error(f"Error checking prefetch for key {key}: {e}")

    def _start_prefetch(self, key: str):
        """启动预取任务"""
        if key not in self._prefetch_tasks:
            task = asyncio.create_task(self._prefetch(key))
            self._prefetch_tasks[key] = task
            task.add_done_callback(lambda _: self._prefetch_tasks.pop(key, None))

    async def _prefetch(self, key: str):
        """预取数据"""
        try:
            # 这里需要实现实际的数据加载逻辑
            # 可以通过回调函数或其他机制获取数据
            pass
        except Exception as e:
            logger.error(f"Error prefetching key {key}: {e}")


class BatchProcessor:
    """批处理器"""

    def __init__(
        self,
        cache: CacheBackend,
        batch_size: int = 100,
        max_delay: float = 0.01,  # 最大延迟（秒）
    ):
        self.cache = cache
        self.batch_size = batch_size
        self.max_delay = max_delay
        self._pending_gets: Dict[str, asyncio.Future] = {}
        self._pending_sets: Dict[str, Tuple[Any, Optional[int]]] = {}
        self._batch_task: Optional[asyncio.Task] = None

    async def get(self, key: str) -> Any:
        """批量获取"""
        if key in self._pending_gets:
            return await self._pending_gets[key]

        future = asyncio.Future()
        self._pending_gets[key] = future

        if len(self._pending_gets) >= self.batch_size:
            await self._process_batch()
        elif self._batch_task is None:
            self._batch_task = asyncio.create_task(self._delayed_process())

        return await future

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """批量设置"""
        self._pending_sets[key] = (value, expire)

        if len(self._pending_sets) >= self.batch_size:
            await self._process_batch()
        elif self._batch_task is None:
            self._batch_task = asyncio.create_task(self._delayed_process())

    async def _delayed_process(self):
        """延迟处理"""
        await asyncio.sleep(self.max_delay)
        await self._process_batch()

    async def _process_batch(self):
        """处理批次"""
        if self._batch_task:
            self._batch_task.cancel()
            self._batch_task = None

        # 处理获取操作
        if self._pending_gets:
            keys = list(self._pending_gets.keys())
            try:
                results = await self.cache.get_many(keys)
                for key in keys:
                    future = self._pending_gets.pop(key)
                    if not future.done():
                        future.set_result(results.get(key))
            except Exception as e:
                for future in self._pending_gets.values():
                    if not future.done():
                        future.set_exception(e)
                self._pending_gets.clear()

        # 处理设置操作
        if self._pending_sets:
            try:
                await self.cache.set_many(
                    {k: v for k, (v, _) in self._pending_sets.items()},
                    expire=next((e for _, e in self._pending_sets.values() if e is not None), None),
                )
            except Exception as e:
                logger.error(f"Error in batch set: {e}")
            finally:
                self._pending_sets.clear()
