"""
缓存系统基础类型定义

此模块提供缓存系统使用的基础类型定义，用于避免循环导入
"""

from typing import Protocol, Any, Optional, Dict, List, Set, Union
from datetime import timedelta


class CacheBackendProtocol(Protocol):
    """缓存后端协议"""
    
    async def init(self) -> None:
        """初始化缓存系统"""
        ...

    async def close(self) -> None:
        """关闭缓存系统"""
        ...

    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None,
        **kwargs
    ) -> bool:
        """设置缓存值"""
        ...

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        ...

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        ...

    async def clear(self) -> bool:
        """清空缓存"""
        ... 