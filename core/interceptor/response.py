# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：base_response.py
@Author  ：PySuper
@Date    ：2024/12/23 18:08 
@Desc    ：Speedy base_response.py
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ResponseSchema(BaseModel, Generic[DataT]):
    """统一响应模型"""

    code: int = 200
    message: str = "success"
    data: Optional[DataT] = None

    class Config:
        json_encoders = {
            # 自定义JSON编码器
        }


class PaginationSchema(BaseModel):
    """分页信息"""

    page: int
    size: int
    total: int
    pages: int


class PageResponseSchema(ResponseSchema, Generic[DataT]):
    """分页响应模型"""

    pagination: Optional[PaginationSchema] = None


def success(data: Any = None, message: str = "success", code: int = 200) -> ResponseSchema:
    """成功响应"""
    return ResponseSchema(code=code, message=message, data=data)


def error(message: str = "error", code: int = 500, data: Any = None) -> ResponseSchema:
    """错误响应"""
    return ResponseSchema(code=code, message=message, data=data)


def page_response(
    items: list,
    total: int,
    page: int,
    size: int,
    message: str = "success",
    code: int = 200,
) -> PageResponseSchema:
    """分页响应"""
    pages = (total + size - 1) // size
    pagination = PaginationSchema(page=page, size=size, total=total, pages=pages)
    return PageResponseSchema(code=code, message=message, data=items, pagination=pagination)
