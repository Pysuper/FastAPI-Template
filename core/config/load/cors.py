# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：cors.py
@Author  ：PySuper
@Date    ：2024-12-28 02:10
@Desc    ：Speedy cors
"""
import json
from typing import List

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class CORSConfig(BaseModel):
    """
    CORS 配置
    """

    allow_origin: List[str] = Field(default=["*"], description="允许的源")
    allow_methods: List[str] = Field(default=["*"], description="允许的方法")
    allow_headers: List[str] = Field(default=["*"], description="允许的头部")
    allow_credentials: bool = Field(default=True, description="是否允许凭证")
    max_age: int = 3600
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("allow_origin", "allow_headers", "allow_methods", mode="before")
    def assemble_list(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [i.strip() for i in v.split(",")]
        return v
