# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：rate.py
@Author  ：PySuper
@Date    ：2024-12-28 02:11
@Desc    ：Speedy rate
"""
from typing import Set

from pydantic import BaseModel, Field


class RateLimiterConfig(BaseModel):
    """
    API 限流配置
    """

    enabled: bool = True
    limit: int = 100  # 请求次数
    window: int = 60  # 时间窗口，单位秒
    key_func: str = "ip"  # 限流依据，可选 ip、user_id、ip_user_id
    exclude_paths: list = []
    RATE_LIMIT_LIMIT: int = 100  # 请求次数
    RATE_LIMIT_REQUESTS: int = 60  # 时间窗口，单位秒
    RATE_LIMIT_KEY_FUNC: str = "ip"  # 限流依据，可选 ip、user_id、ip_user_id
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用限流")
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=100, description="最大请求数")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="时间窗口(秒)")
    RATE_LIMIT_EXCLUDE_PATHS: Set[str] = Field(default={"/docs", "/redoc", "/openapi.json"}, description="限流排除路径")
