from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Integer, Text, Boolean, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.db.core.base import AbstractModel


class LogLevel(str, PyEnum):
    """日志级别"""

    DEBUG = "debug"  # 调试
    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重


class LogType(str, PyEnum):
    """日志类型"""

    SYSTEM = "system"  # 系统日志
    OPERATION = "operation"  # 操作日志
    LOGIN = "login"  # 登录日志
    SECURITY = "security"  # 安全日志
    ERROR = "error"  # 错误日志


class SystemLog(AbstractModel):
    """系统日志模型"""

    __tablename__ = "system_logs"

    # 基本信息
    level: Mapped[LogLevel] = mapped_column(nullable=False, index=True, comment="日志级别")
    type: Mapped[LogType] = mapped_column(nullable=False, index=True, comment="日志类型")
    module: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="模块名称")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="日志消息")

    # 错误信息
    trace: Mapped[Optional[str]] = mapped_column(Text, comment="堆栈跟踪")
    error_code: Mapped[Optional[str]] = mapped_column(String(50), comment="错误代码")
    error_type: Mapped[Optional[str]] = mapped_column(String(100), comment="错误类型")
    error_detail: Mapped[Optional[str]] = mapped_column(Text, comment="错误详情")

    # 请求信息
    request_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, comment="请求ID")
    request_method: Mapped[Optional[str]] = mapped_column(String(10), comment="请求方法")
    request_path: Mapped[Optional[str]] = mapped_column(String(500), comment="请求路径")
    request_params: Mapped[Optional[dict]] = mapped_column(JSON, comment="请求参数")
    request_ip: Mapped[Optional[str]] = mapped_column(String(50), comment="请求IP")
    request_ua: Mapped[Optional[str]] = mapped_column(String(500), comment="User Agent")

    # 用户信息
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, comment="用户ID")
    username: Mapped[Optional[str]] = mapped_column(String(50), index=True, comment="用户名")
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, comment="租户ID")

    # 其他信息
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已解决")
    resolve_time: Mapped[Optional[datetime]] = mapped_column(comment="解决时间")
    resolve_note: Mapped[Optional[str]] = mapped_column(Text, comment="解决说明")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")

    # 索引
    __table_args__ = (
        Index("ix_system_logs_level_type", "level", "type"),
        Index("ix_system_logs_module_level", "module", "level"),
        Index("ix_system_logs_user", "user_id", "username"),
        # {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<SystemLog {self.level} {self.module} {self.message[:50]}>"
