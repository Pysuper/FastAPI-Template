"""
缓存配置模块

    灵活: 支持多种缓存策略和配置选项
    可靠: 增强的验证和错误处理
    可维护: 清晰的结构和文档
    可扩展: 模块化设计便于添加新功能
    实用: 提供了许多开箱即用的功能
"""

import os
from datetime import timedelta
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from core.cache.base.enums import CacheStrategy, CacheLevel, SerializationFormat
from core.cache.exceptions import CacheConfigError


class MemoryConfig(BaseModel):
    """内存缓存配置"""

    max_size: int = Field(default=10000, ge=1, description="最大缓存项数量")
    cleanup_interval: int = Field(default=60, ge=1, description="清理间隔（秒）")
    default_expire: int = Field(default=300, ge=0, description="默认过期时间（秒）")
    enable_lru: bool = Field(default=True, description="是否启用LRU淘汰")
    enable_stats: bool = Field(default=True, description="是否启用统计")

    @field_validator("max_size", "cleanup_interval", "default_expire")
    @classmethod
    def validate_positive(cls, v: int, info: ValidationInfo) -> int:
        if v <= 0:
            raise CacheConfigError(f"{info.field_name} must be positive")
        return v

    def get_ttl(self, ttl: Optional[int] = None) -> int:
        """获取TTL"""
        return ttl if ttl is not None else self.default_expire


class RedisConfig(BaseModel):
    """Redis配置"""

    # 基础连接配置
    host: str = Field(default="localhost", description="Redis主机地址")
    port: int = Field(default=your_port, ge=1, le=65535, description="Redis端口")
    db: int = Field(default=4, ge=0, description="Redis数据库索引")
    password: Optional[str] = Field(default="Affect_PySuper", description="Redis密码")

    # 连接池配置
    max_connections: int = Field(default=100, ge=1, description="最大连接数")
    socket_timeout: float = Field(default=2.0, ge=0, description="Socket超时时间（秒）")
    socket_connect_timeout: float = Field(default=2.0, ge=0, description="连接超时时间（秒）")
    socket_keepalive: bool = Field(default=True, description="是否保持连接")
    health_check_interval: int = Field(default=30, ge=0, description="健康检查间隔（秒）")
    redis_pool_size: int = Field(default=1, description="Redis连接池大小")
    redis_pool_timeout: float = Field(default=30.0, ge=0, description="Redis连接池超时时间（秒）")
    redis_pool_min_size: int = Field(default=0, description="Redis连接池最小大小")
    redis_pool_max_idle_time: float = Field(default=300.0, description="Redis连接池最大空闲时间（秒）")
    redis_retry_on_timeout: bool = Field(default=True, description="是否重试超时")

    # 重试配置
    retry_on_timeout: bool = Field(default=True, description="超时是否重试")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    retry_interval: float = Field(default=0.1, ge=0, description="重试间隔（秒）")

    # 编码配置
    encoding: str = Field(default="utf-8", description="编码格式")
    decode_responses: bool = Field(default=True, description="是否解码响应")

    @property
    def connection_url(self) -> str:
        """获取Redis连接URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    @property
    def connection_kwargs(self) -> Dict[str, Any]:
        """获取Redis连接参数"""
        return {
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "socket_keepalive": self.socket_keepalive,
            "health_check_interval": self.health_check_interval,
            "retry_on_timeout": self.retry_on_timeout,
            "encoding": self.encoding,
            "decode_responses": self.decode_responses,
        }

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int, info: ValidationInfo) -> int:
        if not 1 <= v <= 65535:
            raise CacheConfigError("port must be between 1 and 65535")
        return v


class LocalConfig(BaseModel):
    """本地缓存配置"""

    enable: bool = Field(default=True, description="是否启用本地缓存")
    path: str = Field(default=os.path.join(os.path.expanduser("~"), ".cache"), description="本地缓存路径")
    max_size: int = Field(default=10000, ge=1, description="最大缓存项数量")
    cleanup_interval: int = Field(default=60, ge=1, description="清理间隔（秒）")
    default_expire: int = Field(default=300, ge=0, description="默认过期时间（秒）")
    enable_lru: bool = Field(default=True, description="是否启用LRU淘汰")
    enable_stats: bool = Field(default=True, description="是否启用统计")
    enable_compression: bool = Field(default=True, description="是否启用压缩")
    enable_auto_gc: bool = Field(default=True, description="是否启用自动GC")
    enable_auto_gc_threshold: float = Field(default=0.75, description="自动GC阈值")
    enable_auto_gc_memory_limit: int = Field(default=0, description="自动GC内存阈值（MB）")
    enable_auto_gc_file_limit: int = Field(default=0, description="自动GC文件数量阈值")


class MultiConfig(BaseModel):
    """多缓存配置"""

    enable: bool = Field(default=True, description="是否启用多缓存")
    local: LocalConfig = Field(default_factory=LocalConfig, description="本地缓存配置")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis缓存配置")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="内存缓存配置")

    class Config:
        env_prefix = "CACHE_MULTI_"
        arbitrary_types_allowed = True


class MonitorConfig(BaseModel):
    """监控配置"""

    collection_interval: int = Field(default=60, ge=1, description="指标收集间隔（秒）")
    retention_days: int = Field(default=30, ge=1, description="指标保留天数")
    alert_cooldown: int = Field(default=3600, ge=0, description="告警冷却时间（秒）")
    enable_metrics: bool = Field(default=True, description="是否启用指标收集")
    enable_tracing: bool = Field(default=True, description="是否启用链路追踪")
    enable_logging: bool = Field(default=True, description="是否启用日志记录")

    class Config:
        env_prefix = "CACHE_MONITOR_"


class CacheConfig(BaseModel):
    """缓存配置"""

    # 基础配置
    backend_type: CacheStrategy = Field(default=CacheStrategy.REDIS, description="缓存后端类型")
    strategy: CacheStrategy = Field(default=CacheStrategy.REDIS, description="缓存策略")
    level: CacheLevel = Field(default=CacheLevel.PRIVATE, description="缓存级别")
    serialization_format: SerializationFormat = Field(default=SerializationFormat.JSON, description="序列化格式")

    # 键配置
    key_prefix: str = Field(default="cache:", description="缓存键前缀")
    version: str = Field(default="v1", description="缓存版本")
    key_separator: str = Field(default=":", description="键分隔符")

    # 功能开关
    enable_memory_cache: bool = Field(default=True, description="是否启用内存缓存")
    enable_redis_cache: bool = Field(default=True, description="是否启用Redis缓存")
    enable_stats: bool = Field(default=True, description="是否启用统计")

    # 子配置
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="内存缓存配置")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis配置")
    monitor: MonitorConfig = Field(default_factory=MonitorConfig, description="监控配置")

    # 锁配置
    lock_timeout: int = Field(default=30, ge=0, description="锁超时时间（秒）")
    lock_blocking_timeout: int = Field(default=10, ge=0, description="锁等待超时时间（秒）")
    lock_sleep: float = Field(default=0.1, ge=0, description="锁轮询间隔（秒）")

    # TODO：项目配置，待优化
    CACHE_MAX_SIZE: int = Field(default=10000, description="缓存容量")
    CACHE_CLEANUP_INTERVAL: int = Field(default=60, description="清理间隔（秒）")
    CACHE_DEFAULT_TIMEOUT: int = Field(default=300, description="默认过期时间")
    ENABLE_MEMORY_CACHE: bool = Field(default=True, description="是否启用本地缓存")
    ENABLE_REDIS_CACHE: bool = Field(default=True, description="是否启用Redis缓存")
    ENABLE_CACHE: bool = Field(default=True, description="是否启用缓存")
    CACHE_TYPE: str = Field(default="redis", description="缓存类型")
    CACHE_KEY_PREFIX: str = Field(default="cache:", description="缓存键前缀")
    CACHE_VERSION: str = Field(default="v1", description="缓存版本")
    CACHE_TTL: int = Field(default=3600, description="缓存过期时间")
    CACHE_SERIALIZER: str = Field(default="json", description="缓存序列化格式")
    CACHE_LEVEL: str = Field(default="private", description="缓存级别")
    CACHE_LOCK_TIMEOUT: int = Field(default=30, description="缓存锁超时时间")
    CACHE_MAX_RETRIES: int = Field(default=3, description="缓存最大重试次数")
    CACHE_RETRY_INTERVAL: int = Field(default=1, description="缓存重试间隔")
    CACHE_LOCK_SLEEP: float = Field(default=0.1, description="缓存锁等待时间")
    CACHE_INITIAL_DELAY: int = Field(default=1, description="缓存初始延迟时间")
    CACHE_MAX_DELAY: int = Field(default=10, description="缓存最大延迟时间")
    CACHE_BACKOFF_FACTOR: float = Field(default=0.3, description="缓存延迟因子")
    CACHE_ENABLE_MEMORY_CACHE: bool = Field(default=True, description="是否启用本地缓存")
    CACHE_ENABLE_REDIS_CACHE: bool = Field(default=True, description="是否启用Redis缓存")
    CACHE_MONITOR_INTERVAL: int = Field(default=60, description="Celery任务监控间隔")
    CACHE_MONITOR_EXPIRED_TASKS: bool = Field(default=True, description="是否监控过期任务")
    CACHE_MONITOR_EXPIRED_TASKS_THRESHOLD: int = Field(default=3600, description="过期任务阈值")
    CACHE_MONITOR_EXPIRED_TASKS_CLEANUP_INTERVAL: int = Field(default=3600, description="过期任务清理间隔")
    CACHE_MONITOR_RETENTION_DAYS: int = Field(default=30, description="过期任务保留天数")
    CACHE_MONITOR_CLEANUP_INTERVAL: int = Field(default=3600, description="过期任务清理间隔")
    CACHE_MONITOR_ALERT_COOLDOWN: int = Field(default=3600, description="监控告警冷却时间")

    # TODO：补充，待整合
    # 基础配置
    HOST: str = Field(default="localhost", description="Redis主机")
    PORT: int = Field(default=your_port, description="Redis端口")
    PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    DB: int = Field(default=0, description="Redis数据库")

    # 连接池配置
    POOL_SIZE: int = Field(default=10, description="连接池大小")
    POOL_TIMEOUT: int = Field(default=5, description="连接池超时时间")
    SOCKET_TIMEOUT: int = Field(default=5, description="Socket超时时间")
    SOCKET_CONNECT_TIMEOUT: int = Field(default=5, description="Socket连接超时时间")

    # 重试配置
    MAX_RETRIES: int = Field(default=3, description="最大重试次数")
    RETRY_INTERVAL: int = Field(default=1, description="重试间隔")

    # 缓存配置
    KEY_PREFIX: str = Field(default="cache:", description="缓存键前缀")
    DEFAULT_TIMEOUT: int = Field(default=300, description="默认过期时间")

    @property
    def connection_url(self) -> str:
        """获取Redis连接URL"""
        auth = f":{self.PASSWORD}@" if self.PASSWORD else "@"
        return f"redis://{auth}{self.HOST}:{self.PORT}/{self.DB}"

    @property
    def connection_kwargs(self) -> Dict:
        """获取Redis连接参数"""
        return {
            "max_connections": self.POOL_SIZE,
            "socket_timeout": self.SOCKET_TIMEOUT,
            "socket_connect_timeout": self.SOCKET_CONNECT_TIMEOUT,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }

    @model_validator(mode="after")
    def validate_strategy(self) -> "CacheConfig":
        """验证缓存策略"""
        if self.strategy == CacheStrategy.MEMORY and not self.enable_memory_cache:
            raise CacheConfigError("Memory cache must be enabled when using MEMORY strategy")
        if self.strategy == CacheStrategy.REDIS and not self.enable_redis_cache:
            raise CacheConfigError("Redis cache must be enabled when using REDIS strategy")
        if self.strategy == CacheStrategy.BOTH and not (self.enable_memory_cache and self.enable_redis_cache):
            raise CacheConfigError("Both memory and redis cache must be enabled when using BOTH strategy")
        return self

    def get_cache_key(self, key: str, namespace: Optional[str] = None) -> str:
        """生成缓存键"""
        parts = [self.key_prefix, self.version]
        if namespace:
            parts.append(namespace)
        parts.append(key)
        return self.key_separator.join(parts)

    def get_ttl(self, ttl: Optional[Union[int, timedelta]] = None) -> int:
        """获取TTL（秒）"""
        if ttl is None:
            return self.memory.default_expire
        if isinstance(ttl, timedelta):
            return int(ttl.total_seconds())
        return ttl

    @classmethod
    def from_env(cls) -> "CacheConfig":
        """从环境变量加载配置"""
        env_settings = {}
        for key, value in os.environ.items():
            if key.startswith(cls.Config.env_prefix):
                key = key[len(cls.Config.env_prefix) :].lower()
                key = key.replace(cls.Config.env_nested_delimiter, ".")
                try:
                    if value.lower() in ("true", "false"):
                        value = value.lower() == "true"
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace(".", "", 1).isdigit():
                        value = float(value)
                except ValueError:
                    pass
                env_settings[key] = value
        return cls(**env_settings)

    class Config:
        env_prefix = "CACHE_"
        env_nested_delimiter = "__"
        use_enum_values = True


class CeleryConfig(BaseModel):
    """Celery配置"""

    broker_url: str = Field(default="redis://localhost:your_port/1", description="消息代理URL")
    result_backend: str = Field(default="redis://localhost:your_port/2", description="结果后端URL")
    task_serializer: str = Field(default="json", description="任务序列化器")
    result_serializer: str = Field(default="json", description="结果序列化器")
    accept_content: List[str] = Field(default=["json"], description="接受的内容类型")
    timezone: str = Field(default="UTC", description="时区")
    enable_utc: bool = Field(default=True, description="是否启用UTC")

    # 工作进程配置
    worker_concurrency: int = Field(default=8, ge=1, description="工作进程数")
    worker_max_tasks_per_child: int = Field(default=100, ge=1, description="每个子进程最大任务数")
    worker_prefetch_multiplier: int = Field(default=4, ge=1, description="预取乘数")

    # 任务配置
    task_acks_late: bool = Field(default=True, description="是否延迟确认")
    task_reject_on_worker_lost: bool = Field(default=True, description="工作进程丢失时是否拒绝任务")
    task_track_started: bool = Field(default=True, description="是否跟踪任务开始")

    class Config:
        env_prefix = "CELERY_"
