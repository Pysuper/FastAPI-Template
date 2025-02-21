from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel
from models.audit_log import AuditLogRecord

# 用户-角色关联表
users_roles = Table(
    "users_roles",
    AbstractModel.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.now, nullable=False),
    Column("create_by", Integer, ForeignKey("users.id", ondelete="SET NULL")),
    Index("ix_users_roles_user", "user_id"),
    Index("ix_users_roles_role", "role_id"),
)


class UserStatus(str, PyEnum):
    """用户状态"""

    ACTIVE = "active"  # 正常
    INACTIVE = "inactive"  # 未激活
    DISABLED = "disabled"  # 禁用
    LOCKED = "locked"  # 锁定
    DELETED = "deleted"  # 已删除


class User(AbstractModel):
    """用户模型"""

    __tablename__ = "users"

    # 基本信息
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True, comment="用户名")
    email: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, comment="邮箱")
    password: Mapped[str] = mapped_column(String(128), nullable=False, comment="密码")
    status: Mapped[UserStatus] = mapped_column(default=UserStatus.INACTIVE, nullable=False, index=True, comment="状态")

    # 用户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否超级管理员")
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否员工")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否验证")

    # 个人信息
    full_name: Mapped[Optional[str]] = mapped_column(String(64), comment="全名")
    phone: Mapped[Optional[str]] = mapped_column(String(16), unique=True, comment="手机号")
    avatar: Mapped[Optional[str]] = mapped_column(String(256), comment="头像")
    gender: Mapped[Optional[str]] = mapped_column(String(10), comment="性别")
    birthday: Mapped[Optional[datetime]] = mapped_column(comment="生日")
    address: Mapped[Optional[str]] = mapped_column(String(256), comment="地址")
    bio: Mapped[Optional[str]] = mapped_column(Text, comment="简介")

    # 安全信息
    password_salt: Mapped[Optional[str]] = mapped_column(String(64), comment="密码盐")
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(comment="密码修改时间")
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, comment="登录失败次数")
    locked_until: Mapped[Optional[datetime]] = mapped_column(comment="锁定截止时间")

    # 登录信息
    last_login: Mapped[Optional[datetime]] = mapped_column(comment="最后登录时间")
    last_active: Mapped[Optional[datetime]] = mapped_column(comment="最后活跃时间")
    last_ip: Mapped[Optional[str]] = mapped_column(String(50), comment="最后登录IP")
    login_count: Mapped[int] = mapped_column(Integer, default=0, comment="登录次数")

    # 组织信息
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), index=True, comment="部门ID"
    )
    position: Mapped[Optional[str]] = mapped_column(String(64), comment="职位")
    employee_id: Mapped[Optional[str]] = mapped_column(String(32), unique=True, comment="工号")

    # 其他信息
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 关联关系
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="users", lazy="select")
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=users_roles,
        primaryjoin="User.id == users_roles.c.user_id",
        secondaryjoin="Role.id == users_roles.c.role_id",
        back_populates="users",
        lazy="select",
    )
    audit_logs: Mapped[List["AuditLogRecord"]] = relationship("AuditLogRecord", back_populates="user", lazy="select")
    approved_attendances: Mapped[List["TeacherAttendance"]] = relationship(
        "TeacherAttendance",
        back_populates="approver",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # 索引
    __table_args__ = (
        Index("ix_users_status_active", "status", "is_active"),
        Index("ix_users_department", "department_id", "is_active"),
        Index("ix_users_login", "last_login", "is_active"),
        {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def has_permission(self, permission_name: str) -> bool:
        """检查用户是否具有特定权限"""
        if self.is_superuser:
            return True
        return any(permission.name == permission_name for role in self.roles for permission in role.permissions)

    def has_role(self, role_name: str) -> bool:
        """检查用户是否具有特定角色"""
        if self.is_superuser:
            return True
        return any(role.name == role_name for role in self.roles)
