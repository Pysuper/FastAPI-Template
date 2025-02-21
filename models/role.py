from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Table, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel
from models.user import users_roles

# 角色-权限关联表
role_permissions = Table(
    "role_permissions",
    AbstractModel.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.now, nullable=False),
    Column("created_by", Integer, ForeignKey("users.id", ondelete="SET NULL")),
    Index("ix_role_permissions_role", "role_id"),
    Index("ix_role_permissions_permission", "permission_id"),
)


class RoleType(str, PyEnum):
    """角色类型"""

    SYSTEM = "system"  # 系统角色
    ORGANIZATION = "organization"  # 组织角色
    DEPARTMENT = "department"  # 部门角色
    PROJECT = "project"  # 项目角色
    CUSTOM = "custom"  # 自定义角色


class Role(AbstractModel):
    """角色模型"""

    __tablename__ = "roles"

    # ID 列
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="角色名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="角色编码")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="角色描述")
    type: Mapped[RoleType] = mapped_column(default=RoleType.CUSTOM, nullable=False, index=True, comment="角色类型")

    # 权限和菜单
    permission_ids: Mapped[List[int]] = mapped_column(JSON, default=list, comment="权限ID列表")
    menu_ids: Mapped[List[int]] = mapped_column(JSON, default=list, comment="菜单ID列表")
    data_scope: Mapped[Optional[str]] = mapped_column(String(50), comment="数据权限范围")

    # 层级关系
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"), index=True, comment="父级角色ID"
    )
    level: Mapped[int] = mapped_column(Integer, default=1, comment="层级")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")

    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否系统角色")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否默认角色")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    parent: Mapped[Optional["Role"]] = relationship("Role", remote_side=[id], back_populates="children", lazy="joined")
    children: Mapped[List["Role"]] = relationship("Role", back_populates="parent", cascade="all, delete-orphan")
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=users_roles,
        primaryjoin="Role.id == users_roles.c.role_id",
        secondaryjoin="User.id == users_roles.c.user_id",
        back_populates="roles",
        lazy="joined",
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="joined",
    )

    # 索引
    __table_args__ = (
        Index("ix_roles_parent_sort", "parent_id", "sort"),
        Index("ix_roles_type_active", "type", "is_active"),
        Index("ix_roles_level", "level", "is_active"),
        # {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<Role {self.code} {self.name}>"
