"""
分库分表管理器
实现数据分片功能
"""

import hashlib
from typing import Any, Dict, List

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from core.config.manager import config_manager


class ShardingManager:
    """分库分表管理器"""

    def __init__(self):
        self.config = config_manager.database
        self._setup_shards()

    def _setup_shards(self):
        """初始化分片"""
        self.shard_engines = {}
        self.shard_sessions = {}

        # 创建分片引擎和会话
        for shard_key, url in self.config.SHARD_DATABASE_URLS.items():
            engine = create_engine(
                url,
                pool_size=self.config.POOL_SIZE,
                max_overflow=self.config.MAX_OVERFLOW,
                pool_timeout=self.config.POOL_TIMEOUT,
                pool_recycle=self.config.POOL_RECYCLE,
            )

            session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

            self.shard_engines[shard_key] = engine
            self.shard_sessions[shard_key] = session

    def get_shard_key(self, value: Any) -> str:
        """
        计算分片键
        :param value: 用于计算分片的值
        :return: 分片键
        """
        # 计算哈希值
        hash_value = int(hashlib.md5(str(value).encode()).hexdigest(), 16)

        # 根据分片数量取模
        shard_count = len(self.shard_engines)
        if shard_count == 0:
            return "default"

        shard_index = hash_value % shard_count
        return f"shard_{shard_index}"

    def get_table_name(self, base_name: str, shard_value: Any) -> str:
        """
        获取分表名
        :param base_name: 基础表名
        :param shard_value: 用于分表的值
        :return: 分表名
        """
        if not self.config.TABLE_SHARDING_ENABLED:
            return base_name

        # 计算表分片
        hash_value = int(hashlib.md5(str(shard_value).encode()).hexdigest(), 16)
        table_index = hash_value % self.config.TABLES_PER_SHARD

        return f"{base_name}_{table_index}"

    def get_shard_session(self, shard_key: str) -> scoped_session:
        """
        获取分片会话
        :param shard_key: 分片键
        :return: 会话对象
        """
        if shard_key not in self.shard_sessions:
            raise ValueError(f"Invalid shard key: {shard_key}")
        return self.shard_sessions[shard_key]

    def get_all_table_names(self, base_name: str) -> List[str]:
        """
        获取所有分表名
        :param base_name: 基础表名
        :return: 分表名列表
        """
        if not self.config.TABLE_SHARDING_ENABLED:
            return [base_name]

        return [f"{base_name}_{i}" for i in range(self.config.TABLES_PER_SHARD)]

    async def execute_all_shards(self, callback, *args, **kwargs) -> Dict[str, Any]:
        """
        在所有分片上执行操作
        :param callback: 回调函数
        :return: 各分片的执行结果
        """
        results = {}
        for shard_key, session in self.shard_sessions.items():
            try:
                result = await callback(session, *args, **kwargs)
                results[shard_key] = result
            except Exception as e:
                results[shard_key] = {"error": str(e)}
        return results

    def dispose(self):
        """释放所有分片连接"""
        for engine in self.shard_engines.values():
            engine.dispose()


# 创建分片管理器实例
sharding_manager = ShardingManager()

# 导出
__all__ = ["sharding_manager"]
