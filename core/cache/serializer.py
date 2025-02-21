"""
序列化器模块

此模块提供了多种序列化器实现，支持：
    1. JSON序列化
    2. Pickle序列化
    3. MessagePack序列化
    4. 压缩序列化
    5. 自定义序列化
    6. 序列化性能优化
    7. 错误处理
    8. 类型安全
"""

import datetime
import decimal
import json
import logging
import pickle
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Dict, Optional, Type, Union

from core.cache.exceptions import CacheSerializationError

try:
    import msgpack

    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

try:
    import orjson

    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False

logger = logging.getLogger(__name__)


class SerializationFormat(Enum):
    """序列化格式"""

    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"
    ORJSON = "orjson"


class SerializerMixin:
    """序列化器混入类，提供通用的序列化方法"""

    @staticmethod
    def _serialize_object(obj: Any) -> Any:
        """序列化复杂对象

        支持:
        - dataclass
        - Enum
        - datetime
        - decimal
        - uuid
        - set
        """
        if is_dataclass(obj):
            return asdict(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, set):
            return list(obj)
        return obj

    @staticmethod
    def _deserialize_object(obj: Any, obj_type: Optional[Type] = None) -> Any:
        """反序列化对象

        支持指定目标类型的反序列化
        """
        if obj_type is not None:
            if issubclass(obj_type, Enum):
                return obj_type(obj)
            elif is_dataclass(obj_type):
                return obj_type(**obj)
            elif obj_type == datetime.datetime:
                return datetime.datetime.fromisoformat(obj)
            elif obj_type == datetime.date:
                return datetime.date.fromisoformat(obj)
            elif obj_type == decimal.Decimal:
                return decimal.Decimal(obj)
            elif obj_type == uuid.UUID:
                return uuid.UUID(obj)
            elif obj_type == set:
                return set(obj)
        return obj


class Serializer(ABC, SerializerMixin):
    """序列化器基类"""

    def __init__(self, encoding: str = "utf-8"):
        """初始化序列化器

        Args:
            encoding: 字符编码
        """
        self.encoding = encoding

    @abstractmethod
    def dumps(self, obj: Any) -> bytes:
        """序列化对象为字节串

        Args:
            obj: 要序列化的对象

        Returns:
            序列化后的字节串

        Raises:
            CacheSerializationError: 序列化失败
        """
        pass

    @abstractmethod
    def loads(self, data: bytes, obj_type: Optional[Type] = None) -> Any:
        """反序列化字节串为对象

        Args:
            data: 要反序列化的字节串
            obj_type: 目标对象类型

        Returns:
            反序列化后的对象

        Raises:
            CacheSerializationError: 反序列化失败
        """
        pass

    def __call__(self, obj: Any) -> bytes:
        """调用序列化器

        Args:
            obj: 要序列化的对象

        Returns:
            序列化后的字节串
        """
        return self.dumps(obj)


class JsonSerializer(Serializer):
    """JSON序列化器"""

    def __init__(self, encoding: str = "utf-8", ensure_ascii: bool = False, indent: Optional[int] = None, **kwargs):
        """初始化JSON序列化器

        Args:
            encoding: 字符编码
            ensure_ascii: 是否确保ASCII输出
            indent: 缩进空格数
            **kwargs: 其他JSON序列化参数
        """
        super().__init__(encoding)
        self.json_kwargs = {"ensure_ascii": ensure_ascii, "indent": indent, **kwargs}

    def dumps(self, obj: Any) -> bytes:
        """序列化为JSON"""
        try:
            obj = self._serialize_object(obj)
            if ORJSON_AVAILABLE:
                return orjson.dumps(obj, option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_DATACLASS)
            return json.dumps(obj, **self.json_kwargs).encode(self.encoding)
        except Exception as e:
            raise CacheSerializationError(f"JSON序列化失败: {e}")

    def loads(self, data: bytes, obj_type: Optional[Type] = None) -> Any:
        """从JSON反序列化"""
        try:
            if ORJSON_AVAILABLE:
                obj = orjson.loads(data)
            else:
                obj = json.loads(data.decode(self.encoding))
            return self._deserialize_object(obj, obj_type)
        except Exception as e:
            raise CacheSerializationError(f"JSON反序列化失败: {e}")


class PickleSerializer(Serializer):
    """Pickle序列化器"""

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL, encoding: str = "latin1", **kwargs):
        """初始化Pickle序列化器

        Args:
            protocol: Pickle协议版本
            encoding: 字符编码
            **kwargs: 其他Pickle序列化参数
        """
        super().__init__(encoding)
        self.protocol = protocol
        self.pickle_kwargs = kwargs

    def dumps(self, obj: Any) -> bytes:
        """序列化为Pickle"""
        try:
            return pickle.dumps(obj, protocol=self.protocol, **self.pickle_kwargs)
        except Exception as e:
            raise CacheSerializationError(f"Pickle序列化失败: {e}")

    def loads(self, data: bytes, obj_type: Optional[Type] = None) -> Any:
        """从Pickle反序列化"""
        try:
            obj = pickle.loads(data)
            return self._deserialize_object(obj, obj_type)
        except Exception as e:
            raise CacheSerializationError(f"Pickle反序列化失败: {e}")


class MsgPackSerializer(Serializer):
    """MessagePack序列化器"""

    def __init__(self, encoding: str = "utf-8", use_bin_type: bool = True, **kwargs):
        """初始化MessagePack序列化器

        Args:
            encoding: 字符编码
            use_bin_type: 是否使用二进制类型
            **kwargs: 其他MessagePack序列化参数
        """
        if not MSGPACK_AVAILABLE:
            raise ImportError("msgpack包未安装，请使用pip install msgpack安装")
        super().__init__(encoding)
        self.msgpack_kwargs = {"use_bin_type": use_bin_type, **kwargs}

    def dumps(self, obj: Any) -> bytes:
        """序列化为MessagePack"""
        try:
            obj = self._serialize_object(obj)
            return msgpack.packb(obj, **self.msgpack_kwargs)
        except Exception as e:
            raise CacheSerializationError(f"MessagePack序列化失败: {e}")

    def loads(self, data: bytes, obj_type: Optional[Type] = None) -> Any:
        """从MessagePack反序列化"""
        try:
            obj = msgpack.unpackb(data, **self.msgpack_kwargs)
            return self._deserialize_object(obj, obj_type)
        except Exception as e:
            raise CacheSerializationError(f"MessagePack反序列化失败: {e}")


class CompressedSerializer(Serializer):
    """压缩序列化器装饰器"""

    def __init__(
        self,
        serializer: Serializer,
        compression_threshold: int = 1024,
        compression_level: int = 6,
        encoding: str = "utf-8",
    ):
        """初始化压缩序列化器

        Args:
            serializer: 基础序列化器
            compression_threshold: 压缩阈值(字节)
            compression_level: 压缩级别(1-9)
            encoding: 字符编码
        """
        super().__init__(encoding)
        self.serializer = serializer
        self.compression_threshold = compression_threshold
        self.compression_level = compression_level

    def dumps(self, obj: Any) -> bytes:
        """压缩序列化"""
        try:
            import zlib

            data = self.serializer.dumps(obj)
            if len(data) >= self.compression_threshold:
                compressed = zlib.compress(data, level=self.compression_level)
                if len(compressed) < len(data):
                    return b"c" + compressed
            return b"r" + data
        except Exception as e:
            raise CacheSerializationError(f"压缩序列化失败: {e}")

    def loads(self, data: bytes, obj_type: Optional[Type] = None) -> Any:
        """解压反序列化"""
        try:
            import zlib

            if not data:
                raise CacheSerializationError("空数据")

            flag, content = data[0:1], data[1:]
            if flag == b"c":
                content = zlib.decompress(content)
            elif flag != b"r":
                raise CacheSerializationError("无效的压缩标记")

            return self.serializer.loads(content, obj_type)
        except Exception as e:
            raise CacheSerializationError(f"解压反序列化失败: {e}")


def create_serializer(
    format: Union[str, SerializationFormat] = SerializationFormat.JSON,
    compress: bool = False,
    compression_threshold: int = 1024,
    compression_level: int = 6,
    encoding: str = "utf-8",
    **kwargs,
) -> Serializer:
    """创建序列化器

    Args:
        format: 序列化格式
        compress: 是否启用压缩
        compression_threshold: 压缩阈值(字节)
        compression_level: 压缩级别(1-9)
        encoding: 字符编码
        **kwargs: 其他序列化参数

    Returns:
        序列化器实例

    Raises:
        ValueError: 未知的序列化格式
    """
    if isinstance(format, str):
        try:
            format = SerializationFormat(format.lower())
        except ValueError:
            raise ValueError(f"未知的序列化格式: {format}")

    serializers: Dict[SerializationFormat, Type[Serializer]] = {
        SerializationFormat.JSON: JsonSerializer,
        SerializationFormat.PICKLE: PickleSerializer,
    }

    if MSGPACK_AVAILABLE:
        serializers[SerializationFormat.MSGPACK] = MsgPackSerializer

    if format not in serializers:
        raise ValueError(f"未知的序列化格式: {format}")

    serializer = serializers[format](encoding=encoding, **kwargs)

    if compress:
        return CompressedSerializer(
            serializer,
            compression_threshold=compression_threshold,
            compression_level=compression_level,
            encoding=encoding,
        )

    return serializer


# 创建默认序列化器实例
json_serializer = JsonSerializer()
pickle_serializer = PickleSerializer()
if MSGPACK_AVAILABLE:
    msgpack_serializer = MsgPackSerializer()


class DefaultSerializer:
    pass
