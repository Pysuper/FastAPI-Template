# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：title.py
@Author  ：PySuper
@Date    ：2024/12/30 17:30 
@Desc    ：标题相关的数据模型

提供标题相关的请求和响应模型，包括:
    - 创建标题
    - 更新标题
    - 标题响应
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TitleBase(BaseModel):
    """标题基础模型"""
    title: str
    content: str
    author_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TitleCreate(TitleBase):
    """创建标题请求模型"""
    pass


class TitleUpdate(BaseModel):
    """更新标题请求模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    author_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TitleResponse(TitleBase):
    """标题响应模型"""
    id: int
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
