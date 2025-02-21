# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：menus.py
@Author  ：PySuper
@Date    ：2024-12-30 20:30
@Desc    ：Speedy menus
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, constr


class MenuCreate(BaseModel):
    """创建菜单请求模型"""

    name: constr(min_length=2, max_length=50)
    path: Optional[str] = None
    component: Optional[str] = None
    redirect: Optional[str] = None
    icon: Optional[str] = None
    title: Optional[str] = None
    parent_id: Optional[int] = None
    sort: Optional[int] = 0
    permission: Optional[str] = None
    is_visible: Optional[bool] = True
    is_cache: Optional[bool] = False
    is_frame: Optional[bool] = False
    is_system: Optional[bool] = False
    remark: Optional[str] = None


class MenuUpdate(BaseModel):
    """更新菜单请求模型"""

    name: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    redirect: Optional[str] = None
    icon: Optional[str] = None
    title: Optional[str] = None
    parent_id: Optional[int] = None
    sort: Optional[int] = None
    permission: Optional[str] = None
    is_visible: Optional[bool] = None
    is_cache: Optional[bool] = None
    is_frame: Optional[bool] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class MenuResponse(BaseModel):
    """菜单响应模型"""

    id: int
    name: str
    path: Optional[str]
    component: Optional[str]
    redirect: Optional[str]
    icon: Optional[str]
    title: Optional[str]
    parent_id: Optional[int]
    sort: int
    level: int
    permission: Optional[str]
    status: str
    is_visible: bool
    is_cache: bool
    is_frame: bool
    is_system: bool
    remark: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
