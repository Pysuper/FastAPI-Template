# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：file.py
@Author  ：PySuper
@Date    ：2024/12/26 09:58 
@Desc    ：Speedy file.py
"""
import json
from typing import List

from pydantic import field_validator

from core.config.load.base import BaseConfig


class FileConfig(BaseConfig):
    """
    文件上传配置
    """

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"]
    THUMBNAIL_SIZE: tuple = (200, 200)
    IMAGE_MAX_DIMENSIONS: tuple = (2000, 2000)
    ENABLE_IMAGE_COMPRESSION: bool = True

    @field_validator("THUMBNAIL_SIZE", "IMAGE_MAX_DIMENSIONS", mode="before")
    def parse_dimensions(cls, v, info):
        if isinstance(v, tuple):
            return v
        if isinstance(v, list):
            if len(v) != 2:
                raise ValueError(f"{info.field_name} must contain exactly 2 values")
            return tuple(v)
        if isinstance(v, str):
            try:
                # 移除所有空白字符
                v = "".join(v.split())

                # 处理 JSON 组格式 [x,y]
                if v.startswith("[") and v.endswith("]"):
                    dimensions = json.loads(v)
                # 处理元组格式 (x,y)
                elif v.startswith("(") and v.endswith(")"):
                    dimensions = [int(x.strip()) for x in v[1:-1].split(",")]
                # 处理逗号分隔格式 x,y
                else:
                    dimensions = [int(x.strip()) for x in v.split(",")]

                if len(dimensions) != 2:
                    raise ValueError(f"{info.field_name} must contain exactly 2 values")
                if not all(isinstance(x, (int, float)) for x in dimensions):
                    raise ValueError(f"{info.field_name} values must be numbers")
                return tuple(map(int, dimensions))
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Invalid {info.field_name} format: {e}")
        raise ValueError(f"{info.field_name} must be a tuple, list, or string")
