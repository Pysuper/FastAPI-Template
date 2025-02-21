from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class MenuType(str, PyEnum):
    """菜单类型"""

    DIRECTORY = "directory"  # 目录
    MENU = "menu"  # 菜单
    BUTTON = "button"  # 按钮
    LINK = "link"  # 外链


class Menu(AbstractModel):
    """菜单模型"""

    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="菜单ID")

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="菜单名称")
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="菜单编码")
    type: Mapped[MenuType] = mapped_column(nullable=False, index=True, comment="菜单类型")
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="显示名称")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="菜单描述")

    # 路由信息
    path: Mapped[Optional[str]] = mapped_column(String(200), comment="路由地址")
    component: Mapped[Optional[str]] = mapped_column(String(200), comment="组件路径")
    redirect: Mapped[Optional[str]] = mapped_column(String(200), comment="重定向地址")
    query: Mapped[Optional[str]] = mapped_column(String(200), comment="路由参数")

    # 显示设置
    icon: Mapped[Optional[str]] = mapped_column(String(100), comment="图标")
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否隐藏")
    is_cache: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否缓存")
    is_affix: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否固定")
    is_link: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否外链")
    is_full: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否全屏")

    # 权限设置
    permission: Mapped[Optional[str]] = mapped_column(String(100), comment="权限标识")
    roles: Mapped[Optional[str]] = mapped_column(String(200), comment="角色列表")
    is_require_auth: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否需要认证")

    # 层级关系
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"), index=True, comment="父菜单ID"
    )
    level: Mapped[int] = mapped_column(Integer, default=1, comment="层级")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")

    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    parent: Mapped[Optional["Menu"]] = relationship("Menu", remote_side=[id], back_populates="children", lazy="joined")
    children: Mapped[List["Menu"]] = relationship("Menu", back_populates="parent", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("ix_menus_parent_sort", "parent_id", "sort"),
        Index("ix_menus_type_active", "type", "is_active"),
        Index("ix_menus_level", "level", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Menu {self.code} {self.title}>"
