"""
Redis-based optimistic lock implementation
"""

import json
from typing import Any

from core.cache.base.interface import OptimisticLock


class RedisOptimisticLock(OptimisticLock):
    """
    基于Redis的乐观锁实现
    """

    def __init__(self, redis_client, serializer=None):
        """
        初始化乐观锁

        Args:
            redis_client: Redis客户端实例
            serializer: 序列化器实例（可选）
        """
        self.redis = redis_client
        self.serializer = serializer or json

    async def get_version(self, key: str) -> int:
        """
        获取数据版本号

        Args:
            key: 键名

        Returns:
            int: 版本号
        """
        version_key = f"{key}:version"
        version = await self.redis.get(version_key)
        return int(version) if version else 0

    async def compare_and_set(self, key: str, value: Any, version: int) -> bool:
        """
        比较并设置值，仅当版本号匹配时才更新

        Args:
            key: 键名
            value: 要设置的值
            version: 期望的版本号

        Returns:
            bool: 是否成功更新
        """
        lua_script = """
        local key = KEYS[1]
        local version_key = KEYS[2]
        local value = ARGV[1]
        local expected_version = tonumber(ARGV[2])
        
        local current_version = tonumber(redis.call('get', version_key) or '0')
        if current_version == expected_version then
            redis.call('set', key, value)
            redis.call('incr', version_key)
            return 1
        end
        return 0
        """

        serialized_value = (
            self.serializer.dumps(value) if hasattr(self.serializer, "dumps") else self.serializer.serialize(value)
        )

        success = await self.redis.eval(
            lua_script,
            keys=[key, f"{key}:version"],
            args=[serialized_value, version],
        )

        return bool(success)

    async def get_with_version(self, key: str) -> tuple[Any, int]:
        """
        获取数据及其版本号

        Args:
            key: 键名

        Returns:
            tuple: (值, 版本号)
        """
        lua_script = """
        local key = KEYS[1]
        local version_key = KEYS[2]
        
        local value = redis.call('get', key)
        local version = redis.call('get', version_key) or '0'
        
        return {value, version}
        """

        result = await self.redis.eval(lua_script, keys=[key, f"{key}:version"])

        value, version = result if result else (None, "0")

        if value is not None:
            value = (
                self.serializer.loads(value)
                if hasattr(self.serializer, "loads")
                else self.serializer.deserialize(value)
            )

        return value, int(version)

    async def delete(self, key: str) -> None:
        """
        删除数据及其版本信息

        Args:
            key: 键名
        """
        await self.redis.delete(key, f"{key}:version")
