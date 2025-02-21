# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：permission.py
@Author  ：PySuper
@Date    ：2024/12/30 17:47 
@Desc    ：Speedy permission.py
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, constr


class PermissionCreate(BaseModel):
    """创建权限请求模型"""

    name: constr(min_length=2, max_length=50)
    code: constr(min_length=2, max_length=50)
    description: Optional[str] = None
    type: str
    parent_id: Optional[int] = None
    module: str
    sort: Optional[int] = 0
    is_system: Optional[bool] = False
    remark: Optional[str] = None


class PermissionUpdate(BaseModel):
    """更新权限请求模型"""

    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[int] = None
    module: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class PermissionResponse(BaseModel):
    """权限响应模型"""

    id: int
    name: str
    code: str
    description: Optional[str]
    type: str
    parent_id: Optional[int]
    module: str
    sort: int
    status: str
    is_system: bool
    remark: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
