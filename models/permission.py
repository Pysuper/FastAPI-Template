from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class PermissionType(str, PyEnum):
    """权限类型"""

    MENU = "menu"  # 菜单
    BUTTON = "button"  # 按钮
    API = "api"  # 接口
    DATA = "data"  # 数据
    FILE = "file"  # 文件


class Permission(AbstractModel):
    """权限模型"""

    __tablename__ = "permissions"

    # ID 列
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="权限名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="权限编码")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="权限描述")

    # 权限类型和范围
    type: Mapped[PermissionType] = mapped_column(nullable=False, index=True, comment="权限类型")
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), index=True, comment="父级权限ID"
    )
    module: Mapped[str] = mapped_column(String(50), nullable=False, comment="所属模块")
    path: Mapped[Optional[str]] = mapped_column(String(200), comment="权限路径")
    method: Mapped[Optional[str]] = mapped_column(String(20), comment="HTTP方法")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")

    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否系统权限")
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否公开权限")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    parent: Mapped[Optional["Permission"]] = relationship(
        "Permission", remote_side=[id], back_populates="children", lazy="joined"
    )
    children: Mapped[List["Permission"]] = relationship(
        "Permission", back_populates="parent", cascade="all, delete-orphan"
    )
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary="role_permissions", back_populates="permissions", lazy="joined"
    )

    # 索引
    __table_args__ = (
        Index("ix_permissions_parent_sort", "parent_id", "sort"),
        Index("ix_permissions_type_active", "type", "is_active"),
        Index("ix_permissions_module", "module", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code} {self.name}>"
