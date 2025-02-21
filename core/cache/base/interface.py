"""
缓存系统接口定义

此模块定义了缓存系统的基础接口和抽象类
"""

from typing import Protocol, Any

from core.cache.base.cache_interface import CacheInterface


class CacheBackend(CacheInterface[Any]):
    """缓存后端基类"""

    pass


class DistributedLock(Protocol):
    """分布式锁协议"""

    async def acquire(self) -> bool:
        """获取锁"""
        pass

    async def release(self) -> None:
        """释放锁"""
        pass


class DistributedSemaphore(Protocol):
    """分布式信号量协议"""

    async def acquire(self) -> bool:
        """获取信号量"""
        pass

    async def release(self) -> None:
        """释放信号量"""
        pass


class DownGradableLock(DistributedLock, Protocol):
    """可降级锁协议"""

    pass


class OptimisticLock(DistributedLock, Protocol):
    """乐观锁协议"""

    pass


class PessimisticLock(DistributedLock, Protocol):
    """悲观锁协议"""

    pass


class RowLock(DistributedLock, Protocol):
    """行级锁协议"""

    pass


class TableLock(DistributedLock, Protocol):
    """表级锁协议"""

    pass
