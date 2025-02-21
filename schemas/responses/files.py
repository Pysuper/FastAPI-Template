# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：files.py
@Author  ：PySuper
@Date    ：2024-12-24 21:41
@Desc    ：Speedy files
"""
from typing import List

from pydantic import BaseModel


class ImportResponse(BaseModel):
    """导入响应模型"""

    total: int
    success: int
    failed: int
    errors: List[dict]


class ExportResponse(BaseModel):
    """导出响应模型"""

    url: str
    filename: str
    size: int
