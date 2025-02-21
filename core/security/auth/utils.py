# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：utils.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：安全工具函数
"""
from datetime import timedelta
from typing import Dict, Any, Optional

from passlib.context import CryptContext

from core.security.jwt import JWTHandler

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_user_token(
    user_id: str,
    user_data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建用户token
    :param user_id: 用户ID
    :param user_data: 用户数据
    :param expires_delta: 过期时间
    :return: token字符串
    """
    return JWTHandler.create_access_token(
        subject=user_id,
        claims=user_data,
        expires_delta=expires_delta
    ) 