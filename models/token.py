# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：token.py
@Author  ：PySuper
@Date    ：2025/1/3 16:50 
@Desc    ：Speedy token.py
"""
from pydantic import BaseModel, Field


class Token(BaseModel):
    """令牌模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")
    expires_in: int = Field(3600, description="过期时间(秒)")