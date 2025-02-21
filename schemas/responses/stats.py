# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：stats.py
@Author  ：PySuper
@Date    ：2024-12-24 21:42
@Desc    ：Speedy stats
"""
from typing import List

from pydantic import BaseModel


class StatsResponse(BaseModel):
    """统计响应模型"""

    total: int
    groups: List[dict]
    summary: dict
