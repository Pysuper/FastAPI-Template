# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：main.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：Speedy main
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from api.v1.api import api_router
from core.cache.config.config import CacheConfig
from core.cache.manager import cache_manager
from core.config.setting import settings
from core.db.manager import db_manager
from core.exceptions.manager import setup_exceptions
from core.loge.manager import logic
from core.middlewares.manager import setup_middlewares
from core.security.manager import security_manager
from core.monitor.manager import monitor_manager
from core.tasks.manager import task_manager
from models import *  # noqa


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    FastAPI lifespan event
    """
    print(" ♻️ Starting lifespan event")
    try:
        # 初始化日志管理器
        await logic.init()

        # 初始化数据库管理器
        await db_manager.init()

        # 初始化缓存管理器
        await cache_manager.init(CacheConfig())

        # 初始化安全管理器
        await security_manager.init()

        # 初始化任务管理器
        # await task_manager.init()

        # 初始化监控管理器
        await monitor_manager.init()
    except Exception as e:
        print(f" ❌ Failed to initialize: {str(e)}")
        raise e

    yield

    print(" ♻️ Closing lifespan event ")
    try:
        # 关闭缓存管理器
        if hasattr(cache_manager, "_backend") and cache_manager._backend:
            await cache_manager.close()

        # 关闭数据库管理器
        await db_manager.close()

        # 关闭其他管理器
        await logic.close()
        await security_manager.close()
        await monitor_manager.close()
        # await task_manager.close()

    except Exception as e:
        print(f" ❌ Failed to shutdown: {str(e)}")
        raise e


app = FastAPI(title=settings.app.project_name, lifespan=lifespan)

setup_exceptions(app)
setup_middlewares(app)

app.include_router(api_router, prefix=settings.app.api_v1_str)
