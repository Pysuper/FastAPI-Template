# from typing import Dict, Optional, List
#
# from pydantic import Field
#
# from core.config.load.base import BaseConfig
#
#
# class RedisConfig(BaseConfig):
#     """Redis配置"""
#
#     # 基础配置
#     HOST: str = Field(default="localhost", description="Redis主机")
#     PORT: int = Field(default=your_port, description="Redis端口")
#     PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
#     DB: int = Field(default=0, description="Redis数据库")
#
#     # 连接池配置
#     POOL_SIZE: int = Field(default=10, description="连接池大小")
#     POOL_TIMEOUT: int = Field(default=5, description="连接池超时时间")
#     SOCKET_TIMEOUT: int = Field(default=5, description="Socket超时时间")
#     SOCKET_CONNECT_TIMEOUT: int = Field(default=5, description="Socket连接超时时间")
#
#     # 重试配置
#     MAX_RETRIES: int = Field(default=3, description="最大重试次数")
#     RETRY_INTERVAL: int = Field(default=1, description="重试间隔")
#
#     # 缓存配置
#     KEY_PREFIX: str = Field(default="cache:", description="缓存键前缀")
#     DEFAULT_TIMEOUT: int = Field(default=300, description="默认过期时间")
#
#     @property
#     def connection_url(self) -> str:
#         """获取Redis连接URL"""
#         auth = f":{self.PASSWORD}@" if self.PASSWORD else "@"
#         return f"redis://{auth}{self.HOST}:{self.PORT}/{self.DB}"
#
#     @property
#     def connection_kwargs(self) -> Dict:
#         """获取Redis连接参数"""
#         return {
#             "max_connections": self.POOL_SIZE,
#             "socket_timeout": self.SOCKET_TIMEOUT,
#             "socket_connect_timeout": self.SOCKET_CONNECT_TIMEOUT,
#             "retry_on_timeout": True,
#             "health_check_interval": 30,
#         }
#
#
# class CacheConfig(BaseConfig):
#     """缓存配置"""
#
#     # 基本配置
#     # strategy: str = CacheStrategy.REDIS.value
#     prefix: str = "cache:"
#     ttl: int = 3600
#     version: str = "v1"
#     # level: str = CacheLevel.PRIVATE.value
#
#     # Redis配置
#     redis_host: str = "localhost"
#     redis_port: int = your_port
#     redis_db: int = 0
#     redis_password: Optional[str] = None
#     redis_pool_size: int = 100
#     redis_pool_timeout: int = 30
#     redis_retry_on_timeout: bool = True
#
#     # 本地缓存配置
#     local_maxsize: int = 1000
#     local_ttl: int = 300
#
#     # 序列化配置
#     # serialization_format: str = SerializationFormat.JSON.value
#
#     # 锁配置
#     lock_timeout: int = 30
#     lock_blocking_timeout: int = 10
#     lock_sleep: float = 0.1
#
#     # 统计配置
#     enable_stats: bool = True
#     stats_interval: int = 60
#
#     # 缓存类型
#     TYPE: str = Field(default="redis", description="缓存类型")
#
#     # 本地缓存配置
#     LOCAL_CACHE_SIZE: int = Field(default=1000, description="本地缓存大小")
#     LOCAL_CACHE_TTL: int = Field(default=60, description="本地缓存TTL")
#     REDIS_MAX_CONNECTIONS: int = Field(default=100, description="Redis最大连接数")
#
#     # Redis配置
#     REDIS: RedisConfig = Field(default_factory=RedisConfig, description="Redis配置")
#     CACHE_MAX_SIZE: int = Field(default=10000, description="缓存容量")
#     CACHE_CLEANUP_INTERVAL: int = Field(default=60, description="清理间隔（秒）")
#     CACHE_DEFAULT_TIMEOUT: int = Field(default=300, description="默认过期时间")
#     ENABLE_MEMORY_CACHE: bool = Field(default=True, description="是否启用本地缓存")
#     ENABLE_REDIS_CACHE: bool = Field(default=True, description="是否启用Redis缓存")
#     ENABLE_CACHE: bool = Field(default=True, description="是否启用缓存")
#     CACHE_TYPE: str = Field(default="redis", description="缓存类型")
#     CACHE_KEY_PREFIX: str = Field(default="cache:", description="缓存键前缀")
#     CACHE_VERSION: str = Field(default="v1", description="缓存版本")
#     CACHE_TTL: int = Field(default=3600, description="缓存过期时间")
#     CACHE_SERIALIZER: str = Field(default="json", description="缓存序列化格式")
#     CACHE_LEVEL: str = Field(default="private", description="缓存级别")
#     CACHE_LOCK_TIMEOUT: int = Field(default=30, description="缓存锁超时时间")
#     CACHE_MAX_RETRIES: int = Field(default=3, description="缓存最大重试次数")
#     CACHE_RETRY_INTERVAL: int = Field(default=1, description="缓存重试间隔")
#     CACHE_LOCK_SLEEP: float = Field(default=0.1, description="缓存锁等待时间")
#     CACHE_INITIAL_DELAY: int = Field(default=1, description="缓存初始延��时间")
#     CACHE_MAX_DELAY: int = Field(default=10, description="缓存最大延迟时间")
#     CACHE_BACKOFF_FACTOR: float = Field(default=0.3, description="缓存延迟因子")
#     CACHE_ENABLE_MEMORY_CACHE: bool = Field(default=True, description="是否启用本地缓存")
#     CACHE_ENABLE_REDIS_CACHE: bool = Field(default=True, description="是否启用Redis缓存")
#     CACHE_MONITOR_INTERVAL: int = Field(default=60, description="Celery任务监控间隔")
#     CACHE_MONITOR_EXPIRED_TASKS: bool = Field(default=True, description="是否监控过期任务")
#     CACHE_MONITOR_EXPIRED_TASKS_THRESHOLD: int = Field(default=3600, description="过期任务阈值")
#     CACHE_MONITOR_EXPIRED_TASKS_CLEANUP_INTERVAL: int = Field(default=3600, description="过期任务清理间隔")
#     CACHE_MONITOR_RETENTION_DAYS: int = Field(default=30, description="过期任务保留天数")
#     CACHE_MONITOR_CLEANUP_INTERVAL: int = Field(default=3600, description="过期任务清理间隔")
#     CACHE_MONITOR_ALERT_COOLDOWN: int = Field(default=3600, description="监控告警冷却时间")
#
#
# class CeleryConfig:
#     """
#     Celery配置
#     """
#
#     CELERY_BROKER_URL: str = "redis://localhost:your_port/1"
#     CELERY_RESULT_BACKEND: str = "redis://localhost:your_port/2"
#     CELERY_TASK_SERIALIZER: str = "json"
#     CELERY_RESULT_SERIALIZER: str = "json"
#     CELERY_ACCEPT_CONTENT: List[str] = ["json"]
#     CELERY_TIMEZONE: str = "UTC"
#     CELERY_ENABLE_UTC: bool = True
#     CELERY_WORKER_CONCURRENCY: int = 8
#     CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 100
#     CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4
#     CELERY_TASK_ACKS_LATE: bool = True
#     CELERY_TASK_REJECT_ON_WORKER_LOST: bool = True
#     CELERY_TASK_TRACK_STARTED: bool = True
