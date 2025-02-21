# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2024-12-28 22:06
@Desc    ：Speedy manager
"""


# TODO: 缓存管理器
from core.cache.config.manager import CacheConfigManager

cache_config_manager = CacheConfigManager()


# 获取 cache 配置
config = cache_config_manager.config

# 获取 cache 实例
cache = cache_config_manager.cache

# 关闭 cache 管理器
cache_config_manager.close()

# TODO: 数据库管理器
from core.db.config.manager import DBConfigManager

db_config_manager = DBConfigManager()

# 获取 db 配置
config = db_config_manager.config

# 获取 db 实例
db = db_config_manager.db

# 关闭 db 管理器
db_config_manager.close()

# TODO: 任务管理器
from core.task.config.manager import TaskConfigManager

task_config_manager = TaskConfigManager()

# 获取 task 配置
config = task_config_manager.config

# 获取 task 实例
task = task_config_manager.task

# 关闭 task 管理器
task_config_manager.close()

# TODO: 日志管理器
from core.log.config.manager import LogConfigManager

log_config_manager = LogConfigManager()

# 获取 log 配置
config = log_config_manager.config

# 获取 log 实例
log = log_config_manager.log

# 关闭 log 管理器
log_config_manager.close()

# TODO: 中间件
from fastapi import Request


async def config_middleware(request: Request, call_next):
    # 加载配置
    config = cache_config_manager.config
    # 将配置添加到请求状态中，以便在整个请求生命周期中使用
    request.state.config = config
    response = await call_next(request)
    return response


# TODO: 安全检查器
from core.secure.checker import SecurityChecker

checker = SecurityChecker()
checker.check(config)
