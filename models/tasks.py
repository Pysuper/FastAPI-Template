# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：tasks.py
@Author  ：PySuper
@Date    ：2024-12-30 20:44
@Desc    ：Speedy tasks
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, BigInteger, Float, String, Text, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.db.core.base import AbstractModel


class Task(AbstractModel):
    """通用任务模型"""

    __tablename__ = "tasks"

    # 基本信息
    title: Mapped[str] = mapped_column(String(256), nullable=False, comment="任务标题")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="任务描述")
    type: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务类型")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级")
    
    # 时间信息
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="开始时间")
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="结束时间")
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="截止时间")
    
    # 状态信息
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="任务状态")
    progress: Mapped[float] = mapped_column(Float, default=0, comment="进度")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    
    # 关联信息
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, comment="创建人ID")
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), comment="负责人ID")
    
    # 其他信息
    data: Mapped[Optional[dict]] = mapped_column(JSON, comment="任务数据")
    remark: Mapped[Optional[str]] = mapped_column(Text, comment="备注")
