"""缓存基类模块

此模块提供了缓存系统的基础抽象类，定义了：
1. 基本的缓存操作接口
2. 键管理机制
3. 过期时间处理
4. 健康检查
5. 统计信息收集
6. 错误处理
7. 监控指标
8. 生命周期管理
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union

from core.cache.config.config import CacheConfig
from core.cache.exceptions import CacheError

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """缓存统计信息

    Attributes:
        hits: 命中次数
        misses: 未命中次数
        total_operations: 总操作数
        failed_operations: 失败操作数
        total_items: 总项目数
        total_memory: 总内存占用(字节)
        evicted_items: 被驱逐的项目数
        expired_items: 过期的项目数
        uptime: 运行时间(秒)
    """

    hits: int = 0
    misses: int = 0
    total_operations: int = 0
    failed_operations: int = 0
    total_items: int = 0
    total_memory: int = 0
    evicted_items: int = 0
    expired_items: int = 0
    uptime: float = 0.0


class BaseCache(ABC):
    """缓存基类

    提供缓存系统的基本功能和接口定义：
        1. 基本的CRUD操作
        2. 批量操作支持
        3. 过期时间管理
        4. 原子操作
        5. 健康检查
        6. 统计信息
        7. 错误处理
        8. 生命周期管理
    """

    def __init__(self, config: CacheConfig):
        """初始化缓存基类

        Args:
            config: 缓存配置对象
        """
        self.config = config
        self._initialized = False
        self._start_time = time.time()
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        self._watched_keys: Set[str] = set()
        self._key_locks: Dict[str, asyncio.Lock] = {}

    @abstractmethod
    async def init(self) -> None:
        """初始化缓存系统"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭缓存系统"""
        pass

    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        exist: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)
            exist: 存在性条件(nx:不存在时设置/xx:存在时设置)
            **kwargs: 额外参数

        Returns:
            是否设置成功
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 缓存键

        Returns:
            键是否存在
        """
        pass

    @abstractmethod
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间

        Args:
            key: 缓存键
            seconds: 过期时间(秒)

        Returns:
            是否设置成功
        """
        pass

    @abstractmethod
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余秒数(-2:不存在/-1:永不过期/>=0:剩余秒数)
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """清空缓存

        Returns:
            是否清空成功
        """
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        pass

    @abstractmethod
    async def set_many(
        self,
        mapping: Dict[str, Any],
        expire: Optional[int] = None,
        exist: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """批量设置多个缓存值

        Args:
            mapping: 键值对字典
            expire: 过期时间(秒)
            exist: 存在性条件
            **kwargs: 额外参数

        Returns:
            是否全部设置成功
        """
        pass

    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """批量删除多个缓存值

        Args:
            keys: 缓存键列表

        Returns:
            删除的键数量
        """
        pass

    @abstractmethod
    async def incr(self, key: str, amount: int = 1) -> int:
        """递增值

        Args:
            key: 缓存键
            amount: 增加量

        Returns:
            增加后的值
        """
        pass

    @abstractmethod
    async def decr(self, key: str, amount: int = 1) -> int:
        """递减值

        Args:
            key: 缓存键
            amount: 减少量

        Returns:
            减少后的值
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """获取缓存状态

        Returns:
            状态信息字典
        """
        pass

    def make_key(self, key: str) -> str:
        """生成完整的缓存键

        Args:
            key: 原始键

        Returns:
            带前缀和版本的完整键
        """
        return f"{self.config.key_prefix}:{self.config.version}:{key}"

    def parse_expire(self, expire: Optional[Union[int, float]]) -> Optional[int]:
        """解析过期时间

        Args:
            expire: 原始过期时间

        Returns:
            处理后的过期时间

        Raises:
            CacheError: 无效的过期时间
        """
        if expire is None:
            return self.config.default_expire
        try:
            expire_int = int(expire)
            if expire_int < 0:
                raise CacheError("过期时间不能为负数")
            return expire_int
        except (TypeError, ValueError) as e:
            raise CacheError(f"无效的过期时间: {e}")

    async def health_check(self) -> bool:
        """健康检查

        Returns:
            是否健康
        """
        try:
            test_key = "__health_check__"
            test_value = "ok"
            await self.set(test_key, test_value, expire=1)
            value = await self.get(test_key)
            return value == test_value
        except Exception as e:
            logger.error("缓存健康检查失败", exc_info=e)
            return False

    async def get_or_set(self, key: str, default_func: callable, expire: Optional[int] = None, **kwargs) -> Any:
        """获取缓存值，不存在则设置

        Args:
            key: 缓存键
            default_func: 默认值生成函数
            expire: 过期时间(秒)
            **kwargs: 额外参数

        Returns:
            缓存值
        """
        value = await self.get(key)
        if value is not None:
            return value

        async with self._get_key_lock(key):
            # 双重检查
            value = await self.get(key)
            if value is not None:
                return value

            value = await default_func()
            if value is not None:
                await self.set(key, value, expire=expire, **kwargs)
            return value

    async def watch(self, key: str) -> None:
        """监视键的变化

        Args:
            key: 要监视的键
        """
        self._watched_keys.add(key)

    async def unwatch(self, key: str) -> None:
        """取消监视键

        Args:
            key: 要取消监视的键
        """
        self._watched_keys.discard(key)

    def _get_key_lock(self, key: str) -> asyncio.Lock:
        """获取键的锁

        Args:
            key: 缓存键

        Returns:
            键对应的锁对象
        """
        if key not in self._key_locks:
            self._key_locks[key] = asyncio.Lock()
        return self._key_locks[key]

    async def get_stats(self) -> CacheStats:
        """获取统计信息

        Returns:
            统计信息对象
        """
        self._stats.uptime = time.time() - self._start_time
        return self._stats

    async def get_keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的键列表

        Args:
            pattern: 匹配模式

        Returns:
            匹配的键列表
        """
        raise NotImplementedError

    async def get_random_key(self) -> Optional[str]:
        """获取随机键

        Returns:
            随机键或None
        """
        raise NotImplementedError

    async def rename(self, key: str, new_key: str) -> bool:
        """重命名键

        Args:
            key: 原键名
            new_key: 新键名

        Returns:
            是否重命名成功
        """
        raise NotImplementedError

    async def persist(self, key: str) -> bool:
        """移除键的过期时间

        Args:
            key: 缓存键

        Returns:
            是否移除成功
        """
        raise NotImplementedError

    async def touch(self, key: str) -> bool:
        """更新键的访问时间

        Args:
            key: 缓存键

        Returns:
            是否更新成功
        """
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> bool:
        """
        清理过期的缓存数据
        
        Returns:
            bool: 清理是否成功
        """
        pass
