# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：subject.py
@Author  ：PySuper
@Date    ：2025/1/3 14:37 
@Desc    ：Speedy subject.py
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SubjectBase(BaseModel):
    """学科基础模型"""

    name: str = Field(..., description="学科名称")
    code: str = Field(..., description="学科代码")
    description: Optional[str] = Field(None, description="学科描述")
    is_active: bool = Field(True, description="是否启用")
    department_id: int = Field(..., description="所属院系ID")


class SubjectCreate(SubjectBase):
    """创建学科请求模型"""

    pass


class SubjectUpdate(BaseModel):
    """更新学科请求模型"""

    name: Optional[str] = Field(None, description="学科名称")
    code: Optional[str] = Field(None, description="学科代码")
    description: Optional[str] = Field(None, description="学科描述")
    is_active: Optional[bool] = Field(None, description="是否启用")
    department_id: Optional[int] = Field(None, description="所属院系ID")


class SubjectResponse(SubjectBase):
    """学科响应模型"""

    id: int = Field(..., description="学科ID")
    create_time: datetime = Field(..., description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True
