# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：config.py
@Author  ：PySuper
@Date    ：2024/12/30 17:51 
@Desc    ：Speedy config.py
"""

from enum import Enum as PyEnum
from typing import Optional, Any

from sqlalchemy import String, Text, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from core.db.core.base import AbstractModel


class ConfigType(str, PyEnum):
    """配置类型"""

    STRING = "string"  # 字符串
    NUMBER = "number"  # 数字
    BOOLEAN = "boolean"  # 布尔值
    JSON = "json"  # JSON
    ARRAY = "array"  # 数组
    OBJECT = "object"  # 对象
    DATE = "date"  # 日期
    TIME = "time"  # 时间
    DATETIME = "datetime"  # 日期时间


class ConfigStatus(str, PyEnum):
    """配置状态"""

    ACTIVE = "active"  # 正常
    DISABLED = "disabled"  # 禁用
    DEPRECATED = "deprecated"  # 已废弃
    TESTING = "testing"  # 测试中


class ConfigGroup(str, PyEnum):
    """配置分组"""

    SYSTEM = "system"  # 系统配置
    SECURITY = "security"  # 安全配置
    EMAIL = "email"  # 邮件配置
    SMS = "sms"  # 短信配置
    STORAGE = "storage"  # 存储配置
    PAYMENT = "payment"  # 支付配置
    CUSTOM = "custom"  # 自定义配置


class Config(AbstractModel):
    """系统配置模型"""

    __tablename__ = "configs"

    # 基本信息
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment="配置键")
    value: Mapped[Any] = mapped_column(JSON, nullable=False, comment="配置值")
    type: Mapped[ConfigType] = mapped_column(nullable=False, index=True, comment="配置类型")
    group: Mapped[ConfigGroup] = mapped_column(nullable=False, index=True, comment="配置分组")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="配置描述")

    # 验证规则
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否必填")
    min_value: Mapped[Optional[float]] = mapped_column(comment="最小值")
    max_value: Mapped[Optional[float]] = mapped_column(comment="最大值")
    pattern: Mapped[Optional[str]] = mapped_column(String(200), comment="验证正则")
    options: Mapped[Optional[dict]] = mapped_column(JSON, comment="可选值")

    # 显示设置
    label: Mapped[Optional[str]] = mapped_column(String(100), comment="显示名称")
    placeholder: Mapped[Optional[str]] = mapped_column(String(200), comment="占位提示")
    help_text: Mapped[Optional[str]] = mapped_column(Text, comment="帮助文本")
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否可见")
    sort_order: Mapped[int] = mapped_column(default=0, comment="排序号")

    # 权限控制
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否公开")
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否只读")
    allowed_roles: Mapped[Optional[list]] = mapped_column(JSON, comment="允许的角色")
    allowed_users: Mapped[Optional[list]] = mapped_column(JSON, comment="允许的用户")

    # 状态信息
    status: Mapped[ConfigStatus] = mapped_column(default=ConfigStatus.ACTIVE, nullable=False, index=True, comment="状态")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否系统配置")
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否加密")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 版本控制
    version: Mapped[int] = mapped_column(default=1, comment="版本号")
    created_by: Mapped[Optional[int]] = mapped_column(comment="创建人ID")
    updated_by: Mapped[Optional[int]] = mapped_column(comment="更新人ID")

    # 索引
    __table_args__ = (
        Index("ix_configs_group_key", "group", "key"),
        Index("ix_configs_type_status", "type", "status"),
        Index("ix_configs_system", "is_system", "status"),
        # {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<Config {self.group}.{self.key}={self.value}>"
