from typing import List, Optional, TypeVar

from pydantic import BaseModel, Field

from schemas.base.response import BaseResponse

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=10, ge=1, le=100, description="每页大小")

    def get_skip(self) -> int:
        """获取跳过的记录数"""
        return (self.page - 1) * self.size

    def get_limit(self) -> int:
        """获取限制数量"""
        return self.size


class PaginationMeta(BaseModel):
    """分页元数据"""

    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class PaginatedResponse(BaseResponse[List[T]]):
    """分页响应模型"""

    meta: Optional[PaginationMeta] = Field(default=None, description="分页元数据")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        size: int,
        message: str = "success",
        code: str = "0",
    ) -> "PaginatedResponse[T]":
        """
        创建分页响应
        :param items: 分页数据
        :param total: 总记录数
        :param page: 当前页码
        :param size: 每页大小
        :param message: 响应消息
        :param code: 响应码
        :return: 分页响应实例
        """
        pages = (total + size - 1) // size
        return cls(
            code=code,
            message=message,
            data=items,
            meta=PaginationMeta(
                total=total,
                page=page,
                size=size,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1,
            ),
        )


# class PaginationParams(BaseModel):
#     """分页参数"""
#
#     page: conint(gt=0) = 1  # 页码
#     size: conint(gt=0, le=100) = 20  # 每页大小
#
#
# class PageResponse(BaseModel, Generic[T]):
#     """分页响应"""
#
#     items: List[T]  # 数据列表
#     total: int  # 总数
#     page: int  # 当前页
#     size: int  # 每页大小
#     pages: int  # 总页数
#     has_next: bool  # 是否有下一页
#     has_prev: bool  # 是否有上一页
#
#     @classmethod
#     def create(cls, items: List[T], total: int, page: int, size: int) -> "PageResponse[T]":
#         """创建分页响应
#         Args:
#             items: 数据列表
#             total: 总数
#             page: 当前页
#             size: 每页大小
#         """
#         pages = (total + size - 1) // size
#         return cls(
#             items=items, total=total, page=page, size=size, pages=pages, has_next=page < pages, has_prev=page > 1
#         )
