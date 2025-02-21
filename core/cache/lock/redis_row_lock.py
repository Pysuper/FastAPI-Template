"""Redis-based row-level lock implementation"""

import uuid
from typing import List

from core.cache.base.interface import RowLock


class RedisRowLock(RowLock):
    """
    基于Redis的行级锁实现

    行级锁是一种基于Redis的分布式锁实现，用于保护特定行的并发访问。
    行级锁的特点是：
    1. 行级锁只针对单个行，不涉及多个行之间的并发访问；
    2. 行级锁是非阻塞的，即如果锁被占用，则申请锁的客户端会被阻塞；
    3. 行级锁可以设置过期时间，避免死锁；
    4. 行级锁可以设置多个客户端同时申请同一行的锁，但只有一个客户端可以成功获取锁；
    5. 行级锁可以设置多个客户端同时申请不同行的锁，但只有一个客户端可以成功获取锁。

    行级锁的实现原理：
    1. 客户端申请锁时，会生成一个随机的UUID作为锁的ID；
    2. 客户端会将锁的ID和行ID组成键名，并将锁的ID作为值，同时设置过期时间；
    3. 客户端会将锁的键名加入到一个集合中，集合的键名为表名；
    4. 客户端会尝试获取锁，首先会尝试获取表名对应的集合中所有锁的键名，并判断是否有任何锁的键名与当前客户端的锁的ID相同；
    5. 如果没有相同的锁，则客户端获取锁成功；
    6. 如果有相同的锁，则客户端获取锁失败，并阻塞等待；
    7. 客户端获取锁成功后，会持有锁的状态，直到过期时间到达或客户端主动解锁；
    8. 客户端解锁时，会将锁的键名从集合中删除，并删除锁的键名和值。

    行级锁的优点：
    1. 行级锁可以有效防止并发访问，避免了死锁；
    2. 行级锁可以有效保护数据，避免了数据被多个客户端同时修改。

    行级锁的缺点：
    1. 行级锁的性能比共享锁略差，因为它需要在Redis中维护一个集合；
    2. 行级锁不能跨越多个Redis实例，如果需要跨越多个Redis实例，需要使用基于数据库的分布式锁。

    行级锁的使用方法：
    1. 创建 RedisRowLock的实例，并传入Redis客户端和锁的过期时间；
    2. 调用lock_rows方法，传入表名和行ID列表，尝试锁定所有行；
    3. 如果锁定成功，则可以开始对数据进行操作；
    4. 如果锁定失败，则需要解锁，并重新获取锁；

    示例代码：

    ```python
    import aioredis
    from custom.cache.lock.redis_row_lock import RedisRowLock

    async def main():
        redis = await aioredis.create_redis_pool('redis://localhost')
        lock = RedisRowLock(redis)

        # 尝试锁定行
        success = await lock.lock_rows('my_table', ['row1', 'row2'])
        if success:
            # 开始对数据进行操作
            # ...
            # 解锁
            await lock.unlock_rows('my_table', ['row1', 'row2'])
        else:
            # 重新获取锁
            # ...

    if __name__ == '__main__':
        asyncio.run(main())
    ```

    Args:
        redis_client: Redis客户端实例
        expire: 锁的过期时间（秒）
        owner: 锁的持有者
        rows: 锁保护的行ID列表
    """

    def __init__(self, redis_client, expire: int = 30):
        """
        初始化行级锁

        Args:
            redis_client: Redis客户端实例
            expire: 锁的过期时间（秒）
        """
        self.redis = redis_client
        self.expire = expire
        self._owner = str(uuid.uuid4())

    def _make_lock_key(self, table: str, row_id: str) -> str:
        """
        生成行锁的键名

        Args:
            table: 表名
            row_id: 行ID

        Returns:
            str: 锁键名
        """
        return f"row_lock:{table}:{row_id}"

    def _make_table_key(self, table: str) -> str:
        """
        生成表的键名

        Args:
            table: 表名

        Returns:
            str: 表键名
        """
        return f"row_lock:{table}:rows"

    async def lock_rows(self, table: str, row_ids: List[str]) -> bool:
        """
        锁定指定行

        Args:
            table: 表名
            row_ids: 行ID列表

        Returns:
            bool: 是否成功锁定所有行
        """
        lua_script = """
        local table_key = KEYS[1]
        local owner = ARGV[1]
        local expire = tonumber(ARGV[2])
        local success = true
        
        for i=3,#ARGV do
            local lock_key = ARGV[i]
            if redis.call('exists', lock_key) == 1 then
                success = false
                break
            end
        end
        
        if success then
            for i=3,#ARGV do
                local lock_key = ARGV[i]
                redis.call('set', lock_key, owner)
                redis.call('expire', lock_key, expire)
                redis.call('sadd', table_key, lock_key)
            end
            return 1
        end
        return 0
        """

        lock_keys = [self._make_lock_key(table, row_id) for row_id in row_ids]
        table_key = self._make_table_key(table)

        success = await self.redis.eval(
            lua_script,
            keys=[table_key],
            args=[self._owner, self.expire] + lock_keys,
        )

        return bool(success)

    async def unlock_rows(self, table: str, row_ids: List[str]) -> None:
        """
        解锁指定行

        Args:
            table: 表名
            row_ids: 行ID列表
        """
        lua_script = """
        local table_key = KEYS[1]
        local owner = ARGV[1]
        
        for i=2,#ARGV do
            local lock_key = ARGV[i]
            if redis.call('get', lock_key) == owner then
                redis.call('del', lock_key)
                redis.call('srem', table_key, lock_key)
            end
        end
        """

        lock_keys = [self._make_lock_key(table, row_id) for row_id in row_ids]
        table_key = self._make_table_key(table)

        await self.redis.eval(lua_script, keys=[table_key], args=[self._owner] + lock_keys)

    async def is_row_locked(self, table: str, row_id: str) -> bool:
        """
        检查行是否被锁定

        Args:
            table: 表名
            row_id: 行ID

        Returns:
            bool: 行是否被锁定
        """
        lock_key = self._make_lock_key(table, row_id)
        return await self.redis.exists(lock_key)

    async def get_locked_rows(self, table: str) -> List[str]:
        """
        获取当前锁定的所有行ID

        Args:
            table: 表名

        Returns:
            List[str]: 锁定的行ID列表
        """
        table_key = self._make_table_key(table)
        prefix = f"row_lock:{table}:"
        prefix_len = len(prefix)

        locked_keys = await self.redis.smembers(table_key)
        return [key[prefix_len:] for key in locked_keys]

    async def force_unlock_all(self, table: str) -> None:
        """
        强制解锁表中所有行

        Args:
            table: 表名
        """
        table_key = self._make_table_key(table)
        locked_keys = await self.redis.smembers(table_key)

        if locked_keys:
            await self.redis.delete(*locked_keys)
            await self.redis.delete(table_key)
