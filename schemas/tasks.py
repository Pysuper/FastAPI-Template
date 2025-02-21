# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：tasks.py
@Author  ：PySuper
@Date    ：2024-12-30 20:43
@Desc    ：Speedy tasks
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    """创建评价任务请求模型"""

    title: str
    description: Optional[str] = None
    category: str
    start_time: datetime
    end_time: datetime
    target_type: str
    target_id: int
    evaluator_type: str
    indicator_ids: List[int]
    anonymous: Optional[bool] = True
    weight: Optional[float] = 1.0


class TaskUpdate(BaseModel):
    """更新评价任务请求模型"""

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    evaluator_type: Optional[str] = None
    indicator_ids: Optional[List[int]] = None
    anonymous: Optional[bool] = None
    weight: Optional[float] = None
    status: Optional[str] = None


class TaskResponse(BaseModel):
    """评价任务响应模型"""

    id: int
    title: str
    description: Optional[str]
    category: str
    start_time: datetime
    end_time: datetime
    target_type: str
    target_id: int
    evaluator_type: str
    status: str
    indicator_ids: List[int]
    anonymous: bool
    weight: float
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
