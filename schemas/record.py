# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：record.py
@Author  ：PySuper
@Date    ：2024-12-30 20:38
@Desc    ：Speedy record
"""
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class RecordCreate(BaseModel):
    """创建评价记录请求模型"""

    task_id: int
    scores: Dict[int, float]
    comments: Optional[str] = None


class RecordUpdate(BaseModel):
    """更新评价记录请求模型"""

    scores: Optional[Dict[int, float]] = None
    comments: Optional[str] = None
    status: Optional[str] = None


class RecordResponse(BaseModel):
    """评价记录响应模型"""

    id: int
    task_id: int
    evaluator_id: int
    evaluator_type: str
    scores: Dict[int, float]
    total_score: float
    comments: Optional[str]
    status: str
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
