"""Redis-based table-level lock implementation"""

import uuid
from typing import Optional

from core.cache.base.interface import TableLock


class RedisTableLock(TableLock):
    """
    基于Redis的表级锁实现

    表级锁是一种基于Redis的分布式锁，用于控制对同一张表的并发访问。
    """

    LOCK_MODES = {"exclusive": 2, "shared": 1}  # 排他锁  # 共享锁

    def __init__(self, redis_client, expire: int = 30):
        """
        初始化表级锁

        Args:
            redis_client: Redis客户端实例
            expire: 锁的过期时间（秒）
        """
        self.redis = redis_client
        self.expire = expire
        self._owner = str(uuid.uuid4())

    def _make_lock_key(self, table: str) -> str:
        """
        生成表锁的键名

        Args:
            table: 表名

        Returns:
            str: 锁键名
        """
        return f"table_lock:{table}"

    def _make_mode_key(self, table: str) -> str:
        """
        生成锁模式的键名

        Args:
            table: 表名

        Returns:
            str: 模式键名
        """
        return f"table_lock:{table}:mode"

    def _make_owners_key(self, table: str) -> str:
        """
        生成锁持有者集合的键名

        Args:
            table: 表名

        Returns:
            str: 持有者集合键名
        """
        return f"table_lock:{table}:owners"

    async def lock_table(self, table: str, mode: str = "exclusive") -> bool:
        """
        锁定指定表

        Args:
            table: 表名
            mode: 锁定模式 ("exclusive" 或 "shared")

        Returns:
            bool: 是否成功锁定表
        """
        if mode not in self.LOCK_MODES:
            raise ValueError("Invalid lock mode")

        lua_script = """
        local lock_key = KEYS[1]
        local mode_key = KEYS[2]
        local owners_key = KEYS[3]
        local owner = ARGV[1]
        local mode = ARGV[2]
        local mode_value = tonumber(ARGV[3])
        local expire = tonumber(ARGV[4])
        
        -- 检查当前锁模式
        local current_mode = redis.call('get', mode_key)
        
        if not current_mode then
            -- 无锁状态，可以获取任何模式的锁
            redis.call('set', mode_key, mode)
            redis.call('sadd', owners_key, owner)
            redis.call('expire', mode_key, expire)
            redis.call('expire', owners_key, expire)
            return 1
        elseif current_mode == mode and mode == 'shared' then
            -- 当前是共享锁，且请求共享锁，可以添加新的持有者
            redis.call('sadd', owners_key, owner)
            return 1
        end
        
        return 0
        """

        success = await self.redis.eval(
            lua_script,
            keys=[
                self._make_lock_key(table),
                self._make_mode_key(table),
                self._make_owners_key(table),
            ],
            args=[
                self._owner,
                mode,
                self.LOCK_MODES[mode],
                self.expire,
            ],
        )

        return bool(success)

    async def unlock_table(self, table: str) -> None:
        """
        解锁指定表

        Args:
            table: 表名
        """
        lua_script = """
        local mode_key = KEYS[1]
        local owners_key = KEYS[2]
        local owner = ARGV[1]
        
        -- 移除当前持有者
        redis.call('srem', owners_key, owner)
        
        -- 如果没有其他持有者，删除锁
        if redis.call('scard', owners_key) == 0 then
            redis.call('del', mode_key)
            redis.call('del', owners_key)
        end
        """

        await self.redis.eval(
            lua_script,
            keys=[self._make_mode_key(table), self._make_owners_key(table)],
            args=[self._owner],
        )

    async def is_table_locked(self, table: str) -> bool:
        """
        检查表是否被锁定

        Args:
            table: 表名

        Returns:
            bool: 表是否被锁定
        """
        return await self.redis.exists(self._make_mode_key(table))

    async def get_table_lock_mode(self, table: str) -> Optional[str]:
        """
        获取表的锁定模式

        Args:
            table: 表名

        Returns:
            Optional[str]: 锁定模式 ("exclusive" 或 "shared")，如果未锁定则返回None
        """
        mode = await self.redis.get(self._make_mode_key(table))
        return mode.decode() if mode else None

    async def get_lock_owners(self, table: str) -> list:
        """
        获取表锁的所有持有者

        Args:
            table: 表名

        Returns:
            list: 持有者ID列表
        """
        owners = await self.redis.smembers(self._make_owners_key(table))
        return [owner.decode() for owner in owners]

    async def force_unlock(self, table: str) -> None:
        """
        强制解锁表

        Args:
            table: 表名
        """
        await self.redis.delete(self._make_mode_key(table), self._make_owners_key(table))
