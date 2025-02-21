# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：department.py
@Author  ：PySuper
@Date    ：2024/12/30 17:49 
@Desc    ：Speedy department.py
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, constr


class DepartmentCreate(BaseModel):
    """创建部门请求模型"""

    name: constr(min_length=2, max_length=50)
    code: constr(min_length=2, max_length=50)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort: Optional[int] = 0
    leader: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_system: Optional[bool] = False
    remark: Optional[str] = None


class DepartmentUpdate(BaseModel):
    """更新部门请求模型"""

    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort: Optional[int] = None
    leader: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class DepartmentResponse(BaseModel):
    """部门响应模型"""

    id: int
    name: str
    code: str
    description: Optional[str]
    parent_id: Optional[int]
    sort: int
    level: int
    status: str
    is_system: bool
    leader: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    remark: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
