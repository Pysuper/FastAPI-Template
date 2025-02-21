# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：user.py
@Author  ：PySuper
@Date    ：2024-12-30 21:24
@Desc    ：Speedy user
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, constr


class UserCreate(BaseModel):
    """创建用户请求模型"""

    username: constr(min_length=3, max_length=50)
    password: constr(min_length=6, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    avatar: Optional[str] = None
    department_id: Optional[int] = None
    role_ids: List[int] = []
    is_superuser: Optional[bool] = False
    remark: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用户请求模型"""

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    avatar: Optional[str] = None
    department_id: Optional[int] = None
    role_ids: Optional[List[int]] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    """更新用户密码请求模型"""

    old_password: str
    new_password: constr(min_length=6, max_length=50)


class UserResponse(BaseModel):
    """用户响应模型"""

    id: int
    username: str
    email: Optional[str]
    phone: Optional[str]
    real_name: Optional[str]
    avatar: Optional[str]
    status: str
    is_superuser: bool
    last_login: Optional[datetime]
    login_count: int
    department_id: Optional[int]
    role_ids: List[int]
    remark: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    class Config:
        from_attributes = True
