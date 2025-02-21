"""
@Project ：Speedy
@File    ：base.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：数据库基础模型模块

提供了基础的数据库模型类和相关功能，包括:
1. 基础字段定义
2. 数据验证
3. 缓存管理
4. 事件监听
5. JSON处理
6. 数据转换
"""

from datetime import date, datetime
from typing import Any, Dict, Optional, Protocol, Type, TypeVar, runtime_checkable

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, JSON, MetaData, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.db.core.cache import get_cached_model, set_cached_model, setup_cache_events
from core.db.core.utils import setup_timestamp_events

from core.exceptions.http.validation import ModelValidationException
from core.exceptions.system.cache import CacheException

# 类型变量
T = TypeVar("T", bound="AbstractModel")
JsonType = Dict[str, Any]


@runtime_checkable
class ModelProtocol(Protocol):
    """模型协议，定义模型必须实现的方法"""

    id: int

    def to_dict(self) -> Dict[str, Any]: ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any: ...


# 创建命名约定
naming_convention = {
    "ix": "ix_%(column_0_label)s",  # 索引命名规则
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # 唯一约束命名规则
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # 检查约束命名规则
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # 外键命名规则
    "pk": "pk_%(table_name)s",  # 主键命名规则
}

# 创建元数据
metadata = MetaData(naming_convention=naming_convention)


class Base(DeclarativeBase):
    """声明性基类"""

    metadata = metadata
    __allow_unmapped__ = True

    def __init__(self, **kwargs):
        self._validate_kwargs(kwargs)
        super().__init__(**kwargs)

    def _validate_kwargs(self, kwargs: Dict[str, Any]) -> None:
        """验证初始化参数"""
        valid_fields = {c.key for c in self.__table__.columns}
        invalid_fields = set(kwargs.keys()) - valid_fields
        if invalid_fields:
            raise ModelValidationException(f"Invalid fields: {invalid_fields}")


class AbstractModel(Base):
    """
    抽象模型基类
    提供了通用的数据库字段和功能，包括:
        - 基础字段 (ID、编码、名称等)
        - 状态字段 (排序、状态、是否删除等)
        - 租户和部门字段
        - 创建和更新信息
        - 删除信息
        - 版本控制
        - 扩展字段
    """

    __abstract__ = True
    __allow_unmapped__ = True

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 基础信息
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="编码")
    name: Mapped[str] = mapped_column(String(128), index=True, comment="名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="描述")
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    # 排序和状态
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态：0=禁用，1=启用")
    is_delete: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否删除")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="是否有效")

    # 租户和部门
    tenant_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True, comment="租户ID")
    dept_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True, comment="部门ID")

    # 创建信息
    create_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="创建人ID")
    create_by_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="创建人名称")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")

    # 更新信息
    update_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="更新人ID")
    update_by_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="更新人名称")
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    # 删除信息
    delete_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="删除人ID")
    delete_by_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="删除人名称")
    delete_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="删除时间")

    # 版本控制(用于乐观锁)
    version: Mapped[int] = mapped_column(Integer, default=0, comment="版本号")

    # 扩展字段
    ext_json: Mapped[Optional[JsonType]] = mapped_column(JSON, nullable=True, comment="扩展JSON数据")

    # 缓存配置
    _cache_prefix: str = None  # 缓存前缀
    _cache_ttl: int = 3600  # 默认缓存1小时
    _cache_enabled: bool = True  # 是否启用缓存

    def __init__(self, **kwargs):
        """
        初始化模型实例
        :param kwargs: 初始化参数
        :raises ModelValidationException: 当参数验证失败时
        """
        self._validate_init_params(kwargs)
        super().__init__(**kwargs)

    def _validate_init_params(self, params: Dict[str, Any]) -> None:
        """
        验证初始化参数
        :param params: 参数字典
        :raises ModelValidationException: 当参数验证失败时
        """
        try:
            self._validate_kwargs(params)
            self._validate_required_fields(params)
        except Exception as e:
            raise ModelValidationException(f"参数验证失败: {str(e)}")

    def _validate_required_fields(self, params: Dict[str, Any]) -> None:
        """
        验证必填字段
        :param params: 参数字典
        :raises ModelValidationException: 当必填字段缺失时
        """
        required_fields = {c.name for c in self.__table__.columns if not c.nullable}
        missing_fields = required_fields - set(params.keys())
        if missing_fields:
            raise ModelValidationException(f"缺少必填字段: {missing_fields}")

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        :return: 模型字典表示
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            result[column.name] = value
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        从字典创建实例
        :param data: 数据字典
        :return: 模型实例
        :raises ModelValidationException: 当数据验证失败时
        """
        try:
            filtered_data = {key: value for key, value in data.items() if hasattr(cls, key) and value is not None}
            return cls(**filtered_data)
        except Exception as e:
            raise ModelValidationException(f"从字典创建实例失败: {str(e)}")

    def update(self, **kwargs: Any) -> None:
        """
        更新模型属性
        :param kwargs: 要更新的属性
        :raises ModelValidationException: 当更新验证失败时
        """
        try:
            self._validate_update_params(kwargs)
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.version += 1  # 更新版本号
        except Exception as e:
            raise ModelValidationException(f"更新属性失败: {str(e)}")

    def _validate_update_params(self, params: Dict[str, Any]) -> None:
        """
        验证更新参数
        :param params: 更新参数
        :raises ModelValidationException: 当参数验证失败时
        """
        invalid_fields = set(params.keys()) - {c.name for c in self.__table__.columns}
        if invalid_fields:
            raise ModelValidationException(f"无效的更新字段: {invalid_fields}")

    @classmethod
    async def get_by_id(cls: Type[T], id: Any) -> Optional[T]:
        """
        通过ID获取记录，支持缓存
        :param id: 记录ID
        :return: 模型实例或None
        :raises CacheException: 当缓存操作失败时
        """
        try:
            # 尝试从缓存获取
            cached_instance = await get_cached_model(cls, id)
            if cached_instance:
                return cached_instance

            # 从数据库获取
            instance = await cls.get(id)
            if instance:
                await set_cached_model(instance)
            return instance
        except Exception as e:
            raise CacheException(f"获取记录失败: {str(e)}")

    @classmethod
    def __declare_last__(cls) -> None:
        """
        在模型类声明完成后设置事件监听器
        这个方法会在SQLAlchemy完成模型类的设置后自动调用
        """
        setup_cache_events(cls)
        setup_timestamp_events(cls)
