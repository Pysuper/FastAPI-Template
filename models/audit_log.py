# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：audit_log.py
@Author  ：PySuper
@Date    ：2024/12/20 12:59 
@Desc    ：Speedy audit_log.py
"""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.core.base import AbstractModel


class AuditLogRecord(AbstractModel):
    """数据库审计日志记录模型"""

    __tablename__ = "audit_logs"

    # 基本信息
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, comment="用户ID"
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="时间戳")
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="事件类型")
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False, comment="IP地址")

    # 资源信息
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="资源")
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="操作")
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True, comment="状态")

    # 请求信息
    request_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, comment="请求ID")
    request_method: Mapped[str] = mapped_column(String(10), nullable=False, comment="请求方法")
    request_path: Mapped[str] = mapped_column(String(200), nullable=False, comment="请求路径")
    request_query: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, comment="请求参数")
    request_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, comment="请求体")

    # 响应信息
    response_status: Mapped[Optional[int]] = mapped_column(Integer, comment="响应状态码")
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, comment="响应体")
    error_message: Mapped[Optional[str]] = mapped_column(String(500), comment="错误信息")

    # 其他信息
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, comment="元数据")

    # 关联关系
    user = relationship("User", back_populates="audit_logs", lazy="joined")

    # 索引
    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp", "event_type"),
        Index("ix_audit_logs_user", "user_id", "event_type"),
        Index("ix_audit_logs_resource_action", "resource", "action"),
        {"extend_existing": True},  # 允许表已存在
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.event_type}:{self.action} {self.timestamp}>"
