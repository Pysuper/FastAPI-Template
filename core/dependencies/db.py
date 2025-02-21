# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：db.py
@Author  ：PySuper
@Date    ：2024/12/24 16:08 
@Desc    ：Speedy db.py
"""

from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.core.engine import get_sync_db, get_async_db


def sync_db() -> Generator[Session, None, None]:
    """
    同步数据库会话依赖
    """
    for session in get_sync_db():
        yield session


async def async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    异步数据库会话依赖
    """
    async for session in get_async_db():
        yield session
