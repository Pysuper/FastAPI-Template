# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：parent.py
@Author  ：PySuper
@Date    ：2024-12-30 21:39
@Desc    ：Speedy parent
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class ParentType(str, PyEnum):
    """家长类型"""

    FATHER = "father"  # 父亲
    MOTHER = "mother"  # 母亲
    GUARDIAN = "guardian"  # 监护人
    OTHER = "other"  # 其他


class Parent(AbstractModel):
    """家长信息模型"""

    __tablename__ = "parents"

    # 基本信息
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="姓名")
    type: Mapped[ParentType] = mapped_column(nullable=False, index=True, comment="家长类型")
    id_card: Mapped[str] = mapped_column(String(18), unique=True, nullable=False, comment="身份证号")
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="联系电话")
    email: Mapped[Optional[str]] = mapped_column(String(100), comment="电子邮箱")
    address: Mapped[Optional[str]] = mapped_column(String(200), comment="居住地址")
    occupation: Mapped[Optional[str]] = mapped_column(String(100), comment="职业")
    workplace: Mapped[Optional[str]] = mapped_column(String(200), comment="工作单位")

    # 账号信息
    username: Mapped[Optional[str]] = mapped_column(String(32), unique=True, comment="用户名")
    password: Mapped[Optional[str]] = mapped_column(String(128), comment="密码")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    last_login: Mapped[Optional[datetime]] = mapped_column(comment="最后登录时间")

    # 其他信息
    education: Mapped[Optional[str]] = mapped_column(String(50), comment="学历")
    income_level: Mapped[Optional[str]] = mapped_column(String(20), comment="收入水平")
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(20), comment="紧急联系电话")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    students: Mapped[List["Student"]] = relationship("Student", back_populates="parent", lazy="joined")
    feedbacks: Mapped[List["ParentFeedback"]] = relationship(
        "ParentFeedback", back_populates="parent", cascade="all, delete-orphan"
    )
    notification_records: Mapped[List["NotificationRecord"]] = relationship(
        "NotificationRecord", back_populates="parent", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("ix_parents_name_type", "name", "type"),
        Index("ix_parents_phone", "phone"),
        # {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<Parent {self.name} {self.type}>"
