# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：roles.py
@Author  ：PySuper
@Date    ：2024/12/30 17:44 
@Desc    ：Speedy roles.py
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, constr


class RoleCreate(BaseModel):
    """创建角色请求模型"""

    name: constr(min_length=2, max_length=50)
    code: constr(min_length=2, max_length=50)
    description: Optional[str] = None
    permission_ids: List[int] = []
    menu_ids: List[int] = []
    parent_id: Optional[int] = None
    sort: Optional[int] = 0
    is_system: Optional[bool] = False
    remark: Optional[str] = None


class RoleUpdate(BaseModel):
    """更新角色请求模型"""

    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None
    menu_ids: Optional[List[int]] = None
    parent_id: Optional[int] = None
    sort: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class RoleResponse(BaseModel):
    """角色响应模型"""

    id: int
    name: str
    code: str
    description: Optional[str]
    permission_ids: List[int]
    menu_ids: List[int]
    parent_id: Optional[int]
    sort: int
    status: str
    is_system: bool
    remark: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
