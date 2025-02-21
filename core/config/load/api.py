# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：api.py
@Author  ：PySuper
@Date    ：2024/12/26 09:58 
@Desc    ：Speedy api.py
"""

from pydantic import BaseModel


class APIConfig(BaseModel):
    """
    API 基础配置
    """

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    api_v1_str: str = "/api/v1"
    project_name: str = "Speedy"
    version: str = "1.0.0"
    description: str = "Speedy API"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    class Config:
        populate_by_name = True
        str_strip_whitespace = True
        validate_assignment = True
        extra = "allow"
