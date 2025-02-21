"""缓存异常模块

此模块定义了缓存操作相关的所有异常类。
包括连接异常、超时异常、序列化异常等。

每个异常类都继承自基础的CacheError类，
并可以携带原始异常信息。
"""

from typing import Optional, Any, Dict


class CacheError(Exception):
    """基础缓存异常

    所有缓存相关异常的基类。

    Attributes:
        message: 异常信息
        cause: 导致此异常的原始异常
        details: 额外的异常详情
    """

    def __init__(self, message: str, cause: Optional[Exception] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.cause = cause
        self.details = details or {}

    def __str__(self) -> str:
        result = self.message
        if self.cause:
            result += f" (caused by: {str(self.cause)})"
        if self.details:
            result += f" [details: {str(self.details)}]"
        return result


class CacheConnectionError(CacheError):
    """
    缓存连接异常

    当无法连接到缓存服务器时抛出。

    Examples:
        >>> raise CacheConnectionError("无法连接到Redis服务器", details={"host": "localhost", "port": your_port})
    """

    pass


class CacheTimeoutError(CacheError):
    """
    缓存操作超时异常

    当缓存操作超过预设时间限制时抛出。

    Examples:
        >>> raise CacheTimeoutError("操作超时", details={"timeout": 2, "operation": "get"})
    """

    pass


class CacheSerializationError(CacheError):
    """
    缓存序列化/反序列化异常

    当对象无法序列化或反序列化时抛出。

    Examples:
        >>> raise CacheSerializationError("无法序列化对象", details={"object_type": "CustomClass"})
    """

    pass


class CacheKeyError(CacheError):
    """
    缓存键错误

    当缓存键不合法或不存在时抛出。

    Examples:
        >>> raise CacheKeyError("缓存键不存在", details={"key": "user:123"})
    """

    pass


class CacheCapacityError(CacheError):
    """
    缓存容量错误

    当缓存容量达到限制时抛出。

    Examples:
        >>> raise CacheCapacityError("缓存已满", details={"max_size": "1GB", "current_size": "1.1GB"})
    """

    pass


class CacheConfigError(CacheError):
    """
    缓存配置错误

    当缓存配置无效或冲突时抛出。

    Examples:
        >>> raise CacheConfigError("无效的Redis配置", details={"invalid_keys": ["port"]})
    """

    pass


class CacheBackendError(CacheError):
    """
    缓存后端错误

    当特定的缓存后端发生错误时抛出。

    Examples:
        >>> raise CacheBackendError("Redis命令执行失败", details={"command": "SET", "args": ["key", "value"]})
    """

    pass


class CacheLockError(CacheError):
    """
    缓存锁错误

    当分布式锁操作失败时抛出。

    Examples:
        >>> raise CacheLockError("无法获取锁", details={"lock_key": "mutex:123", "timeout": 5})
    """

    pass


class CacheOperationError(CacheError):
    """
    缓存操作错误

    当缓存的基本操作(get/set/delete等)失败时抛出。

    Examples:
        >>> raise CacheOperationError("设置缓存失败", details={"operation": "set", "key": "user:123"})
    """

    pass


class CacheValueError(CacheError):
    """
    缓存值错误

    当缓存值不合法或格式错误时抛出。

    Examples:
        >>> raise CacheValueError("缓存值类型错误", details={"expected": "str", "got": "int"})
    """

    pass


class CachePatternError(CacheError):
    """
    缓存模式错误

    当缓存键模式不合法时抛出。

    Examples:
        >>> raise CachePatternError("无效的键模式", details={"pattern": "user:*:invalid"})
    """

    pass


class CacheAuthenticationError(CacheError):
    """
    缓存认证错误

    当缓存服务器认证失败时抛出。

    Examples:
        >>> raise CacheAuthenticationError("Redis认证失败", details={"user": "cache_user"})
    """

    pass


class CacheEncodingError(CacheError):
    """
    缓存编码错误

    当缓存数据编码/解码失败时抛出。

    Examples:
        >>> raise CacheEncodingError("无法解码缓存值", details={"encoding": "utf-8"})
    """

    pass


class SecurityError(CacheError):
    """安全相关错误"""

    pass


class AccessDeniedError(CacheError):
    """访问被拒绝"""

    pass


class EncryptionError(CacheError):
    """加密错误"""

    pass
