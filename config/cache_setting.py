# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：cache_setting.py
@Author  ：PySuper
@Date    ：2025-01-01 17:19
@Desc    ：Speedy cache_setting
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from core.cache.exceptions import CacheConfigError

logger = logging.getLogger(__name__)


class CacheEnv(Enum):
    """缓存环境"""

    DEV = "dev"  # 开发环境
    TEST = "test"  # 测试环境
    STAGE = "stage"  # 预发布环境
    PROD = "prod"  # 生产环境


class RedisMode(Enum):
    """Redis模式"""

    STANDALONE = "standalone"  # 单机模式
    SENTINEL = "sentinel"  # 哨兵模式
    CLUSTER = "cluster"  # 集群模式


class EvictionPolicy(Enum):
    """驱逐策略"""

    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最不经常使用
    FIFO = "fifo"  # 先进先出
    RANDOM = "random"  # 随机


@dataclass
class RedisSettings:
    """Redis配置"""

    # 基本配置
    host: str = "localhost"
    port: int = your_port
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None
    ssl: bool = False
    ssl_cert_reqs: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None

    # 连接池配置
    pool_size: int = 10
    pool_timeout: int = 30
    pool_retry: int = 3
    pool_idle_timeout: int = 300
    pool_max_connections: int = 0

    # 哨兵配置
    sentinel_master: Optional[str] = None
    sentinel_nodes: List[str] = field(default_factory=list)
    sentinel_password: Optional[str] = None
    sentinel_socket_timeout: float = 1.0

    # 集群配置
    cluster_nodes: List[str] = field(default_factory=list)
    cluster_retry_attempts: int = 3
    cluster_retry_delay: float = 1.0
    cluster_skip_full_coverage_check: bool = False

    # 操作配置
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = False
    retry_on_timeout: bool = True
    retry_on_error: List[str] = field(default_factory=list)
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 30

    # 编码配置
    encoding: str = "utf-8"
    encoding_errors: str = "strict"
    decode_responses: bool = True

    # TLS配置
    tls: bool = False
    tls_cert_reqs: Optional[str] = None
    tls_certfile: Optional[str] = None
    tls_keyfile: Optional[str] = None
    tls_ca_certs: Optional[str] = None
    tls_ciphers: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RedisSettings":
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def validate(self):
        """验证配置"""
        if self.pool_size < 1:
            raise CacheConfigError("连接池大小必须大于0")
        if self.pool_timeout < 0:
            raise CacheConfigError("连接池超时必须大于等于0")
        if self.socket_timeout < 0:
            raise CacheConfigError("套接字超时必须大于等于0")
        if self.max_retries < 0:
            raise CacheConfigError("最大重试次数必须大于等于0")


@dataclass
class MemorySettings:
    """内存缓存配置"""

    # 容量配置
    max_items: Optional[int] = None
    max_memory: Optional[int] = None
    max_item_size: Optional[int] = None

    # 清理配置
    cleanup_interval: int = 300
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    eviction_samples: int = 5
    eviction_threshold: float = 0.9

    # 性能配置
    thread_safe: bool = True
    use_locking: bool = True
    lock_timeout: float = 1.0

    # 压缩配置
    compression: bool = False
    compression_min_size: int = 1024
    compression_threshold: float = 0.3

    # 监控配置
    enable_stats: bool = True
    stats_interval: int = 60

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v.value if isinstance(v, Enum) else v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemorySettings":
        """从字典创建"""
        config = {}
        for k, v in data.items():
            if k in cls.__dataclass_fields__:
                field_type = cls.__dataclass_fields__[k].type
                if field_type == EvictionPolicy:
                    config[k] = EvictionPolicy(v)
                else:
                    config[k] = v
        return cls(**config)

    def validate(self):
        """验证配置"""
        if self.max_items is not None and self.max_items < 0:
            raise CacheConfigError("最大条目数必须大于等于0")
        if self.max_memory is not None and self.max_memory < 0:
            raise CacheConfigError("最大内存必须大于等于0")
        if self.cleanup_interval < 0:
            raise CacheConfigError("清理间隔必须大于等于0")
        if not 0 <= self.eviction_threshold <= 1:
            raise CacheConfigError("驱逐阈值必须在0到1之间")


@dataclass
class ProjectCacheSettings:
    """全局缓存配置"""

    # 环境配置
    env: CacheEnv = CacheEnv.DEV
    debug: bool = False
    testing: bool = False

    # Redis配置
    redis: RedisSettings = field(default_factory=RedisSettings)
    redis_mode: RedisMode = RedisMode.STANDALONE

    # 内存缓存配置
    memory: MemorySettings = field(default_factory=MemorySettings)

    # 键配置
    key_prefix: str = ""
    key_separator: str = ":"
    key_encoding: str = "utf-8"
    key_hash_algorithm: str = "md5"

    # 序列化配置
    default_serializer: str = "json"
    serializer_encoding: str = "utf-8"
    compress_serialization: bool = False
    compression_threshold: int = 1024

    # 过期配置
    default_ttl: Optional[int] = None
    min_ttl: Optional[int] = None
    max_ttl: Optional[int] = None
    ttl_jitter: float = 0.0

    # 重试配置
    retry_enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_jitter: float = 0.1
    retry_codes: Set[int] = field(default_factory=lambda: {-1, -2, -3})

    # 监控配置
    enable_metrics: bool = True
    metrics_interval: int = 60
    metrics_prefix: str = "cache"
    slow_operation_threshold: float = 1.0

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    access_log: bool = True
    error_log: bool = True

    # 安全配置
    encrypt_values: bool = False
    encryption_key: Optional[str] = None
    encryption_algorithm: str = "AES"
    ssl_enabled: bool = False
    ssl_verify: bool = True
    ssl_cert_file: Optional[str] = None
    ssl_key_file: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        # 加载环境变量
        self._load_env_vars()

        # 验证配置
        self.validate()

    def _load_env_vars(self):
        """加载环境变量"""
        # 环境
        if env := os.getenv("CACHE_ENV"):
            self.env = CacheEnv(env.lower())

        # Redis
        if host := os.getenv("REDIS_HOST"):
            self.redis.host = host
        if port := os.getenv("REDIS_PORT"):
            self.redis.port = int(port)
        if password := os.getenv("REDIS_PASSWORD"):
            self.redis.password = password

        # 加密
        if key := os.getenv("CACHE_ENCRYPTION_KEY"):
            self.encryption_key = key

    def load_file(self, path: Union[str, Path]):
        """从文件加载配置

        Args:
            path: 配置文件路径
        """
        path = Path(path)
        if not path.exists():
            raise CacheConfigError(f"配置文件不存在: {path}")

        try:
            with open(path) as f:
                config = json.load(f)

            # 更新Redis配置
            if redis_config := config.get("redis"):
                self.redis = RedisSettings.from_dict(redis_config)

            # 更新内存配置
            if memory_config := config.get("memory"):
                self.memory = MemorySettings.from_dict(memory_config)

            # 更新其他配置
            for k, v in config.items():
                if k not in ("redis", "memory") and hasattr(self, k):
                    setattr(self, k, v)

        except Exception as e:
            raise CacheConfigError(f"加载配置文件失败: {e}")

    def save_file(self, path: Union[str, Path]):
        """保存配置到文件

        Args:
            path: 配置文件路径
        """
        try:
            config = {
                "env": self.env.value,
                "redis": self.redis.to_dict(),
                "memory": self.memory.to_dict(),
                **{k: v for k, v in asdict(self).items() if k not in ("env", "redis", "memory")},
            }

            with open(path, "w") as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            raise CacheConfigError(f"保存配置文件失败: {e}")

    def validate(self):
        """验证配置"""
        # 验证Redis配置
        self.redis.validate()

        # 验证内存配置
        self.memory.validate()

        # 验证TTL配置
        if self.min_ttl is not None and self.max_ttl is not None:
            if self.min_ttl > self.max_ttl:
                raise CacheConfigError("最小TTL不能大于最大TTL")
            if self.default_ttl is not None:
                if not self.min_ttl <= self.default_ttl <= self.max_ttl:
                    raise CacheConfigError("默认TTL必须在最小和最大TTL之间")

        # 验证重试配置
        if self.retry_enabled:
            if self.max_retries < 0:
                raise CacheConfigError("最大重试次数必须大于等于0")
            if self.retry_delay < 0:
                raise CacheConfigError("重试延迟必须大于等于0")
            if not 0 <= self.retry_jitter <= 1:
                raise CacheConfigError("重试抖动必须在0到1之间")

        # 验证加密配置
        if self.encrypt_values and not self.encryption_key:
            raise CacheConfigError("启用加密时必须提供加密密钥")

    def get_redis_url(self) -> str:
        """获取Redis URL

        Returns:
            Redis连接URL
        """
        auth = ""
        if self.redis.username and self.redis.password:
            auth = f"{self.redis.username}:{self.redis.password}@"
        elif self.redis.password:
            auth = f":{self.redis.password}@"

        return f"redis://{auth}{self.redis.host}:{self.redis.port}/{self.redis.db}"

    @property
    def is_production(self) -> bool:
        """是否是生产环境"""
        return self.env == CacheEnv.PROD

    @property
    def is_development(self) -> bool:
        """是否是开发环境"""
        return self.env == CacheEnv.DEV

    @property
    def is_testing(self) -> bool:
        """是否是测试环境"""
        return self.env == CacheEnv.TEST or self.testing
