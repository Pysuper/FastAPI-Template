import hashlib
import json
from typing import Any, Optional

from core.cache.config.config import CacheConfig


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成缓存键
    :param prefix: 前缀
    :param args: 位置参数
    :param kwargs: 关键字参数
    :return: 缓存键
    """
    # 合并参数
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

    # 生成哈希
    key_str = ":".join(key_parts)
    hash_str = hashlib.md5(key_str.encode()).hexdigest()

    return f"{prefix}:{hash_str}"


def serialize_value(value: Any) -> str:
    """
    序列化值
    :param value: 值
    :return: 序列化后的字符串
    """
    try:
        return json.dumps(value)
    except:
        return str(value)


def deserialize_value(value: str) -> Any:
    """
    反序列化值
    :param value: 序列化后的字符串
    :return: 值
    """
    try:
        return json.loads(value)
    except:
        return value


def parse_expire_time(expire: Optional[Any]) -> Optional[int]:
    """
    解析过期时间
    :param expire: 过期时间
    :return: 秒数
    """
    if expire is None:
        return None

    if isinstance(expire, (int, float)):
        return int(expire)

    if hasattr(expire, "total_seconds"):
        return int(expire.total_seconds())

    raise ValueError(f"不支持的过期时间类型: {type(expire)}")


def merge_configs(config1: CacheConfig, config2: CacheConfig) -> CacheConfig:
    """
    合并配置
    :param config1: 配置1
    :param config2: 配置2
    :return: 合并后的配置
    """
    merged = CacheConfig()

    # 合并属性
    for key in dir(config1):
        if not key.startswith("_"):
            value1 = getattr(config1, key)
            value2 = getattr(config2, key, None)
            setattr(merged, key, value2 if value2 is not None else value1)

    return merged
