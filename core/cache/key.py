"""
缓存键管理模块

提供缓存键的生成、验证和管理功能：
    1. 键名生成和规范化
    2. 前缀管理
    3. 命名空间支持
    4. 版本控制
    5. 键验证
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Union

from .exceptions import CacheKeyError


class CacheKey:
    """缓存键管理类

    特性：
    1. 自动添加前缀
    2. 支持命名空间
    3. 版本控制
    4. 键名规范化
    5. 防止键名冲突
    """

    def __init__(
        self,
        prefix: str = "cache:",
        version: str = "v1",
        namespace: Optional[str] = None,
        separator: str = ":",
        max_length: int = 200,
    ):
        """初始化缓存键管理器

        Args:
            prefix: 键前缀
            version: 缓存版本
            namespace: 命名空间
            separator: 分隔符
            max_length: 最大键长度
        """
        self.prefix = prefix
        self.version = version
        self.namespace = namespace
        self.separator = separator
        self.max_length = max_length

    def make_key(
        self,
        key: str,
        namespace: Optional[str] = None,
        version: Optional[str] = None,
    ) -> str:
        """生成完整的缓存键

        Args:
            key: 原始键名
            namespace: 命名空间（覆盖默认值）
            version: 版本（覆盖默认值）

        Returns:
            完整的缓存键

        Raises:
            CacheKeyError: 键名无效
        """
        # 验证键名
        if not key:
            raise CacheKeyError("键名不能为空")

        if not isinstance(key, str):
            raise CacheKeyError(f"键名必须是字符串，而不是 {type(key)}")

        # 构建键名部分
        parts = [
            self.prefix.rstrip(self.separator),
            version or self.version,
        ]

        # 添加命名空间
        ns = namespace or self.namespace
        if ns:
            parts.append(ns)

        # 添加键名
        parts.append(key)

        # 组合完整键名
        full_key = self.separator.join(parts)

        # 验证长度
        if len(full_key) > self.max_length:
            raise CacheKeyError(f"键名过长（{len(full_key)} > {self.max_length}）")

        return full_key

    def make_key_for_args(
        self,
        base_key: str,
        args: tuple,
        kwargs: Dict[str, Any],
        namespace: Optional[str] = None,
    ) -> str:
        """为函数参数生成缓存键

        Args:
            base_key: 基础键名
            args: 位置参数
            kwargs: 关键字参数
            namespace: 命名空间

        Returns:
            包含参数信息的缓存键
        """
        # 序列化参数
        key_parts = [base_key]

        if args:
            key_parts.append(self._serialize_args(args))

        if kwargs:
            key_parts.append(self._serialize_kwargs(kwargs))

        # 组合键名
        key = self.separator.join(key_parts)

        # 如果键名过长，使用哈希值
        if len(key) > self.max_length:
            key = self._make_hash_key(key)

        return self.make_key(key, namespace)

    def make_pattern(
        self,
        pattern: str,
        namespace: Optional[str] = None,
        version: Optional[str] = None,
    ) -> str:
        """生成用于模式匹配的键

        Args:
            pattern: 匹配模式
            namespace: 命名空间
            version: 版本

        Returns:
            完整的匹配模式
        """
        parts = [
            self.prefix.rstrip(self.separator),
            version or self.version,
        ]

        if namespace or self.namespace:
            parts.append(namespace or self.namespace)

        parts.append(pattern)

        return self.separator.join(parts)

    def _serialize_args(self, args: tuple) -> str:
        """序列化位置参数"""
        return hashlib.md5(json.dumps(args).encode()).hexdigest()

    def _serialize_kwargs(self, kwargs: Dict[str, Any]) -> str:
        """序列化关键字参数"""
        # 排序以确保相同的参数生成相同的键
        sorted_items = sorted(kwargs.items())
        return hashlib.md5(json.dumps(sorted_items).encode()).hexdigest()

    def _make_hash_key(self, key: str) -> str:
        """生成键的哈希值"""
        return hashlib.md5(key.encode()).hexdigest()

    def validate_key(self, key: str) -> bool:
        """验证键名是否有效

        Args:
            key: 待验证的键名

        Returns:
            是否有效

        Raises:
            CacheKeyError: 键名无效
        """
        if not isinstance(key, str):
            raise CacheKeyError(f"键名必须是字符串，而不是 {type(key)}")

        if not key:
            raise CacheKeyError("键名不能为空")

        if len(key) > self.max_length:
            raise CacheKeyError(f"键名过长（{len(key)} > {self.max_length}）")

        return True

    def extract_namespace(self, key: str) -> Optional[str]:
        """从完整键名中提取命名空间

        Args:
            key: 完整的缓存键

        Returns:
            命名空间，如果没有则返回None
        """
        parts = key.split(self.separator)
        if len(parts) >= 4:  # prefix:version:namespace:key
            return parts[2]
        return None

    def extract_version(self, key: str) -> Optional[str]:
        """从完整键名中提取版本

        Args:
            key: 完整的缓存键

        Returns:
            版本号，如果没有则返回None
        """
        parts = key.split(self.separator)
        if len(parts) >= 3:  # prefix:version:key
            return parts[1]
        return None

    def strip_prefix(self, key: str) -> str:
        """移除键名中的前缀

        Args:
            key: 完整的缓存键

        Returns:
            不含前缀的键名
        """
        if key.startswith(self.prefix):
            return key[len(self.prefix) :]
        return key
