from typing import Generic, List, TypeVar

from pydantic import BaseModel, conint

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数"""

    page: conint(gt=0) = 1  # 页码
    size: conint(gt=0, le=100) = 20  # 每页大小


class PageResponse(BaseModel, Generic[T]):
    """分页响应"""

    items: List[T]  # 数据列表
    total: int  # 总数
    page: int  # 当前页
    size: int  # 每页大小
    pages: int  # 总页数
    has_next: bool  # 是否有下一页
    has_prev: bool  # 是否有上一页

    @classmethod
    def create(cls, items: List[T], total: int, page: int, size: int) -> "PageResponse[T]":
        """创建分页响应
        Args:
            items: 数据列表
            total: 总数
            page: 当前页
            size: 每页大小
        """
        pages = (total + size - 1) // size
        return cls(
            items=items, total=total, page=page, size=size, pages=pages, has_next=page < pages, has_prev=page > 1
        )
