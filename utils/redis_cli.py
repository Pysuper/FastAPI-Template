from datetime import timedelta
from typing import Any, Optional, Union

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError

from core.config.setting import settings
from core.loge.manager import logic as logger

settings = settings.cache


class RedisClient:
    """Redis 客户端工具类"""

    _instance = None
    _pool = None
    client: Optional[Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def init(self):
        """初始化 Redis 连接池和客户端"""
        if self._pool is None:
            self._pool = ConnectionPool(
                host=settings.redis.host,
                port=settings.redis.port,
                db=settings.redis.db,
                password=settings.redis.password or None,
                max_connections=settings.redis.max_connections,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout,
                retry_on_timeout=settings.redis.retry_on_timeout,
                health_check_interval=30,
                encoding=settings.redis.encoding,
                decode_responses=settings.redis.decode_responses,
            )
            self.client = Redis(connection_pool=self._pool)

    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        try:
            if not self.client:
                await self.init()
            return await self.client.get(key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(
        self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None, nx: bool = False, xx: bool = False
    ) -> bool:
        """设置值"""
        try:
            if not self.client:
                await self.init()
            return await self.client.set(key, str(value), ex=expire, nx=nx, xx=xx)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除键"""
        try:
            if not self.client:
                await self.init()
            return bool(await self.client.delete(key))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            if not self.client:
                await self.init()
            return bool(await self.client.exists(key))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            if not self.client:
                await self.init()
            return bool(await self.client.expire(key, seconds))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis expire error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        try:
            if not self.client:
                await self.init()
            return await self.client.ttl(key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis ttl error: {e}")
            return -2

    async def incr(self, key: str) -> Optional[int]:
        """递增"""
        try:
            if not self.client:
                await self.init()
            return await self.client.incr(key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis incr error: {e}")
            return None

    async def decr(self, key: str) -> Optional[int]:
        """递减"""
        try:
            if not self.client:
                await self.init()
            return await self.client.decr(key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis decr error: {e}")
            return None

    async def hset(self, name: str, key: str, value: Any) -> Optional[int]:
        """设置哈希表字段"""
        try:
            if not self.client:
                await self.init()
            return await self.client.hset(name, key, str(value))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis hset error: {e}")
            return None

    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希表字段"""
        try:
            if not self.client:
                await self.init()
            return await self.client.hget(name, key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis hget error: {e}")
            return None

    async def hdel(self, name: str, *keys: str) -> Optional[int]:
        """删除哈希表字段"""
        try:
            if not self.client:
                await self.init()
            return await self.client.hdel(name, *keys)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis hdel error: {e}")
            return None

    async def hgetall(self, name: str) -> Optional[dict]:
        """获取哈希表所有字段"""
        try:
            if not self.client:
                await self.init()
            return await self.client.hgetall(name)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis hgetall error: {e}")
            return None

    async def sadd(self, name: str, *values: Any) -> Optional[int]:
        """添加集合成员"""
        try:
            if not self.client:
                await self.init()
            return await self.client.sadd(name, *values)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis sadd error: {e}")
            return None

    async def srem(self, name: str, *values: Any) -> Optional[int]:
        """移除集合成员"""
        try:
            if not self.client:
                await self.init()
            return await self.client.srem(name, *values)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis srem error: {e}")
            return None

    async def smembers(self, name: str) -> Optional[set]:
        """获取集合所有成员"""
        try:
            if not self.client:
                await self.init()
            return await self.client.smembers(name)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis smembers error: {e}")
            return None

    async def zadd(self, name: str, mapping: dict) -> Optional[int]:
        """添加有序集合成员"""
        try:
            if not self.client:
                await self.init()
            return await self.client.zadd(name, mapping)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis zadd error: {e}")
            return None

    async def zrange(self, name: str, start: int, end: int, desc: bool = False) -> Optional[list]:
        """获取有序集合范围内的成员"""
        try:
            if not self.client:
                await self.init()
            return await self.client.zrange(name, start, end, desc=desc)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis zrange error: {e}")
            return None

    async def pipeline(self) -> Any:
        """获取管道"""
        try:
            if not self.client:
                await self.init()
            return await self.client.pipeline()
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis pipeline error: {e}")
            return None

    async def close(self):
        """关闭连接"""
        try:
            if self.client:
                await self.client.close()
            if self._pool:
                await self._pool.disconnect()
        except Exception as e:
            logger.error(f"Redis close error: {e}")

    async def ping(self) -> bool:
        """检查连接是否正常"""
        try:
            if not self.client:
                await self.init()
            return await self.client.ping()
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis ping error: {e}")
            return False

    async def health_check(self) -> dict:
        """健康检查"""
        status = await self.ping()
        return {
            "status": "healthy" if status else "unhealthy",
            "details": {
                "connected": status,
                "host": settings.redis.host,
                "port": settings.redis.port,
                "db": settings.redis.db,
            },
        }


# 创建全局 Redis 客户端实例
redis_client = RedisClient()
