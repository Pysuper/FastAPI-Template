"""
缓存预热模块
"""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Callable, Union

from cache.exceptions import CacheError
from core.cache.base.interface import CacheBackend

logger = logging.getLogger(__name__)


class CacheWarmer:
    """缓存预热器"""

    def __init__(
        self,
        cache: CacheBackend,
        batch_size: int = 100,
        concurrency: int = 5,
    ):
        self.cache = cache
        self.batch_size = batch_size
        self.concurrency = concurrency
        self._warming = False
        self._stats = {
            "total_keys": 0,
            "loaded_keys": 0,
            "failed_keys": 0,
            "skipped_keys": 0,
        }

    async def warm_up(
        self,
        keys: List[str],
        data_loader: Callable[[List[str]], Any],
        expire: Optional[Union[int, timedelta]] = None,
        force: bool = False,
    ) -> Dict[str, int]:
        """预热指定的缓存键

        Args:
            keys: 要预热的键列表
            data_loader: 数据加载函数，接收键列表返回��据
            expire: 缓存过期时间
            force: 是否强制预热（忽略已存在的键）

        Returns:
            Dict[str, int]: 预热统计信息
        """
        if self._warming:
            raise CacheError("Cache warming is already in progress")

        self._warming = True
        self._reset_stats()
        self._stats["total_keys"] = len(keys)

        try:
            # 分批处理键
            for i in range(0, len(keys), self.batch_size):
                batch_keys = keys[i : i + self.batch_size]

                # 如果不强制预热，先检查哪些键已存在
                if not force:
                    existing_keys = []
                    for key in batch_keys:
                        if await self.cache.exists(key):
                            existing_keys.append(key)
                            self._stats["skipped_keys"] += 1

                    # 从批次中移除已存在的键
                    batch_keys = [k for k in batch_keys if k not in existing_keys]

                if not batch_keys:
                    continue

                # 创建协程任务
                tasks = []
                for j in range(0, len(batch_keys), self.concurrency):
                    concurrent_keys = batch_keys[j : j + self.concurrency]
                    tasks.append(self._warm_batch(concurrent_keys, data_loader, expire))

                # 并发执行任务
                await asyncio.gather(*tasks)

            return self._stats
        finally:
            self._warming = False

    async def _warm_batch(
        self,
        keys: List[str],
        data_loader: Callable[[List[str]], Any],
        expire: Optional[Union[int, timedelta]] = None,
    ):
        """预热一批键

        Args:
            keys: 键列表
            data_loader: 数据加载函数
            expire: 过期时间
        """
        try:
            # 加载数据
            data = await data_loader(keys)

            # 写入缓存
            if isinstance(data, dict):
                success = await self.cache.set_many(data, expire=expire)
                if success:
                    self._stats["loaded_keys"] += len(data)
                else:
                    self._stats["failed_keys"] += len(keys)
            else:
                logger.warning(f"Data loader returned invalid format for keys: {keys}")
                self._stats["failed_keys"] += len(keys)
        except Exception as e:
            logger.error(f"Error warming cache batch: {e}")
            self._stats["failed_keys"] += len(keys)

    def _reset_stats(self):
        """重置统计信息"""
        self._stats = {"total_keys": 0, "loaded_keys": 0, "failed_keys": 0, "skipped_keys": 0}

    @property
    def stats(self) -> Dict[str, int]:
        """获取预热统计信息"""
        return self._stats.copy()

    @property
    def is_warming(self) -> bool:
        """是否正在预热"""
        return self._warming
