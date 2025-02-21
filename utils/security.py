# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：security.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：Speedy security
"""
from datetime import datetime, timedelta
from typing import Dict, Optional

import bcrypt
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext

from core.config.setting import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# 模拟的令牌黑名单
revoked_tokens: Dict[str, datetime] = {}


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """验证密码"""
#     return pwd_context.verify(plain_password, hashed_password)


# def get_password_hash(password: str) -> str:
#     """获取密码哈希"""
#     return pwd_context.hash(password)


def get_password_hash(password: str) -> str:
    """生成密码哈希值

    Args:
        password: 原始密码

    Returns:
        密码哈希值
    """
    # 使用 bcrypt 直接生成哈希
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """验证密码

    Args:
        plain_password: 原始密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    if not hashed_password:
        return False

    # 使用 bcrypt 直接验证
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def is_token_revoked(token: str) -> bool:
    """检查令牌是否已被吊销"""
    return token in revoked_tokens


def revoke_token(token: str) -> None:
    """吊销令牌"""
    try:
        payload = jwt.decode(token, settings.security.SECRET_KEY, algorithms=[settings.security.ALGORITHM])
        revoked_tokens[token] = payload.get("exp", datetime.now())
    except JWTError:
        pass


def verify_totp(token: str, secret: str) -> bool:
    """验证TOTP令牌"""
    # 这里可以使用pyotp库来验证TOTP
    import pyotp

    totp = pyotp.TOTP(secret)
    return totp.verify(token)


def generate_totp_secret() -> str:
    """生成TOTP密钥"""
    import pyotp

    return pyotp.random_base32()


# 在创建访问令牌时检查是否已吊销
async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.security.SECRET_KEY, algorithm=settings.security.ALGORITHM)
    if is_token_revoked(encoded_jwt):
        raise ValueError("Token has been revoked")
    return encoded_jwt


# 在创建刷新令牌时检查是否已吊销
async def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=settings.security.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.security.SECRET_KEY, algorithm=settings.security.ALGORITHM)
    if is_token_revoked(encoded_jwt):
        raise ValueError("Token has been revoked")
    return encoded_jwt


def generate_verification_code(length: int = 6) -> str:
    """生成随机验证码

    Args:
        length: 验证码长度,默认6位

    Returns:
        str: 生成的数字验证码
    """
    import random

    # 生成指定长度的随机数字验证码
    code = "".join(str(random.randint(0, 9)) for _ in range(length))
    return code
