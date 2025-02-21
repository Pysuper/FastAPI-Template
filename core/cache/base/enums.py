# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：enums.py
@Author  ：PySuper
@Date    ：2025/1/2 10:29 
@Desc    ：Speedy enums.py
"""

from enum import Enum, auto


class CacheStrategy(str, Enum):
    """缓存策略"""

    LOCAL = "local"  # 本地缓存
    MEMORY = "memory"  # 内存缓存
    REDIS = "redis"  # Redis缓存
    MULTI = "multi"  # 多级缓存
    BOTH = "both"  # 多种缓存
    NONE = "none"  # 无缓存


class CacheBackendType(Enum):
    """缓存后端类型"""

    MEMORY = auto()  # 内存缓存
    REDIS = auto()  # Redis
    MEMCACHED = auto()  # Memcached
    MULTI = auto()  # 多级缓存
    LOCAL = auto()  # 本地缓存
    BOTH = auto()  # Redis和内存缓存
    NONE = auto()  # 无缓存


class CacheMode(Enum):
    """缓存模式"""

    READ_WRITE = "read_write"  # 读写模式
    READ_ONLY = "read_only"  # 只读模式
    WRITE_ONLY = "write_only"  # 只写模式


class CacheLevel(str, Enum):
    """缓存级别"""

    PRIVATE = "private"  # 私有缓存
    SHARED = "shared"  # 共享缓存
    GLOBAL = "global"  # 全局缓存


class SerializationFormat(str, Enum):
    """序列化格式"""

    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"
