"""
缓存接口定义

此模块定义了缓存系统的基础接口，用于避免循环导入
"""

from datetime import timedelta
from typing import Protocol, Any, Optional, Dict, List, Union, TypeVar, Generic

T = TypeVar("T")


class CacheInterface(Protocol, Generic[T]):
    """缓存接口协议"""

    async def get(self, key: str, default: T = None) -> Optional[T]:
        """获取缓存值"""
        pass

    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """设置缓存值"""
        pass

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass

    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """设置过期时间"""
        pass

    async def ttl(self, key: str) -> Optional[int]:
        """获取剩余过期时间"""
        pass

    async def clear(self) -> bool:
        """清空缓存"""
        pass

    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """批量获取缓存值"""
        pass

    async def set_many(
        self,
        mapping: Dict[str, T],
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """批量设置缓存值"""
        pass

    async def delete_many(self, keys: List[str]) -> bool:
        """批量删除缓存值"""
        pass

    async def incr(self, key: str, delta: int = 1) -> int:
        """递增计数器"""
        pass

    async def decr(self, key: str, delta: int = 1) -> int:
        """递减计数器"""
        pass

    async def get_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        pass
