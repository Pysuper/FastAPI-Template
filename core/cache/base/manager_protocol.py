"""
缓存管理器协议定义

此模块定义了缓存管理器的接口协议，用于避免循环导入
"""

from datetime import timedelta
from typing import Protocol, Any, Optional, Union


class CacheManagerProtocol(Protocol):
    """缓存管理器协议"""

    async def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """获取缓存值"""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """设置缓存值"""
        ...

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        ...

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        ...

    @property
    def config(self) -> Any:
        """获取配置"""
        ...
