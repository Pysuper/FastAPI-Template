"""
@Project ：Speedy
@File    ：pagination.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：分页管理器模块

提供了高效的分页查询功能，包括:
    - 标准分页查询
    - 游标分页查询
    - 键集分页查询
    - 分页参数验证
    - 分页结果封装
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, Union

from pydantic import BaseModel, conint, validator
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

from core.config.manager import config_manager
from core.db.core.base import AbstractModel

# 类型变量
T = TypeVar("T")
Model = TypeVar("Model", bound=AbstractModel)


class PaginationError(Exception):
    """分页错误"""

    pass


@dataclass
class PaginationMeta:
    """
    分页元数据
    用于存储分页查询的元信息
    """

    page: int  # 当前页码
    size: int  # 每页大小
    total: Optional[int] = None  # 总记录数
    pages: Optional[int] = None  # 总页数
    has_next: bool = False  # 是否有下一页
    has_prev: bool = False  # 是否有上一页
    next_cursor: Any = None  # 下一页游标
    prev_cursor: Any = None  # 上一页游标

    def __post_init__(self):
        """初始化后处理"""
        if self.total is not None:
            self.pages = (self.total + self.size - 1) // self.size
            self.has_next = self.page < self.pages
            self.has_prev = self.page > 1


class PageParams(BaseModel):
    """
    分页参数基类
    定义了基本的分页参数验证规则
    """

    page: conint(gt=0) = 1  # 页码
    size: conint(gt=0, le=100) = 20  # 每页大小

    @validator("size")
    def validate_size(cls, v: int) -> int:
        """验证每页大小不超过系统配置的最大值"""
        max_size = config_manager.database.MAX_PER_PAGE
        if v > max_size:
            raise ValueError(f"每页大小不能超过 {max_size}")
        return v


class CursorParams(BaseModel):
    """
    游标分页参数
    支持基于游标的分页查询
    """

    cursor: Optional[Any] = None  # 游标值
    size: conint(gt=0, le=100) = 20  # 每页大小
    ascending: bool = True  # 是否升序

    @validator("size")
    def validate_size(cls, v: int) -> int:
        """验证每页大小不超过系统配置的最大值"""
        max_size = config_manager.database.MAX_PER_PAGE
        if v > max_size:
            raise ValueError(f"每页大小不能超过 {max_size}")
        return v


class PaginationResult(Generic[T]):
    """
    分页结果封装
    提供了统一的分页结果格式
    """

    def __init__(self, items: List[T], meta: PaginationMeta):
        self.items = items
        self.meta = meta

    def dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "items": self.items,
            "meta": {
                "page": self.meta.page,
                "size": self.meta.size,
                "total": self.meta.total,
                "pages": self.meta.pages,
                "has_next": self.meta.has_next,
                "has_prev": self.meta.has_prev,
                "next_cursor": self.meta.next_cursor,
                "prev_cursor": self.meta.prev_cursor,
            },
        }


class PaginationManager:
    """
    分页管理器
    提供了多种分页查询方式的实现
    """

    def __init__(self):
        """初始化分页管理器"""
        self.config = config_manager.database

    async def paginate(
        self, query: Union[Query, Select], params: PageParams, count_total: bool = True
    ) -> PaginationResult[Model]:
        """
        标准分页查询
        :param query: 查询对象
        :param params: 分页参数
        :param count_total: 是否计算总数
        :return: 分页结果
        :raises PaginationError: 当分页查询失败时
        """
        try:
            # 验证参数
            page = max(1, params.page)
            per_page = min(max(1, params.size), self.config.MAX_PER_PAGE)

            # 计算总数
            total = None
            if count_total:
                total = await query.with_entities(func.count()).scalar()

            # 计算偏移量
            offset = (page - 1) * per_page

            # 获取分页数据
            items = await query.offset(offset).limit(per_page).all()

            # 创建分页元数据
            meta = PaginationMeta(page=page, size=per_page, total=total)

            return PaginationResult(items=items, meta=meta)
        except Exception as e:
            raise PaginationError(f"分页查询失败: {str(e)}")

    async def cursor_paginate(
        self,
        query: Union[Query, Select],
        params: CursorParams,
        cursor_field: str,
    ) -> PaginationResult[Model]:
        """
        游标分页查询
        :param query: 查询对象
        :param params: 游标分页参数
        :param cursor_field: 游标字段名
        :return: 分页结果
        :raises PaginationError: 当游标分页查询失败时
        """
        try:
            # 验证参数
            per_page = min(max(1, params.size), self.config.MAX_PER_PAGE)

            # 添加游标过滤
            if params.cursor is not None:
                model = query.column_descriptions[0]["type"]
                field = getattr(model, cursor_field)
                if params.ascending:
                    query = query.filter(field > params.cursor)
                else:
                    query = query.filter(field < params.cursor)

            # 添加排序
            query = query.order_by(asc(cursor_field) if params.ascending else desc(cursor_field))

            # 获取数据
            items = await query.limit(per_page + 1).all()

            # 检查是否有下一页
            has_next = len(items) > per_page
            if has_next:
                items = items[:-1]

            # 获取下一个游标值
            next_cursor = None
            if has_next and items:
                next_cursor = getattr(items[-1], cursor_field)

            # 创建分页元数据
            meta = PaginationMeta(
                page=1, size=per_page, has_next=has_next, next_cursor=next_cursor  # 游标分页不使用页码
            )

            return PaginationResult(items=items, meta=meta)
        except Exception as e:
            raise PaginationError(f"游标分页查询失败: {str(e)}")

    async def keyset_paginate(
        self,
        query: Union[Query, Select],
        sort_fields: List[Tuple[str, bool]],
        last_values: Optional[List[Any]] = None,
        size: int = 20,
    ) -> PaginationResult[Model]:
        """
        键集分页查询
        :param query: 查询对象
        :param sort_fields: 排序字段列表，每个元素为(字段名, 是否升序)
        :param last_values: 上一页最后一条记录的排序字段值
        :param size: 每页大小
        :return: 分页结果
        :raises PaginationError: 当键集分页查询失败时
        """
        try:
            # 验证参数
            per_page = min(max(1, size), self.config.MAX_PER_PAGE)

            # 添加排序
            model = query.column_descriptions[0]["type"]
            for field_name, ascending in sort_fields:
                field = getattr(model, field_name)
                query = query.order_by(asc(field) if ascending else desc(field))

            # 添加键集过滤
            if last_values:
                conditions = []
                for i, (field_name, ascending) in enumerate(sort_fields):
                    field = getattr(model, field_name)
                    value = last_values[i]

                    if i == 0:
                        conditions.append(field > value if ascending else field < value)
                    else:
                        prev_conditions = []
                        for j in range(i):
                            prev_field = getattr(model, sort_fields[j][0])
                            prev_value = last_values[j]
                            prev_conditions.append(prev_field == prev_value)
                        conditions.append((field > value if ascending else field < value) & func.and_(*prev_conditions))

                query = query.filter(func.or_(*conditions))

            # 获取数据
            items = await query.limit(per_page + 1).all()

            # 检查是否有下一页
            has_next = len(items) > per_page
            if has_next:
                items = items[:-1]

            # 获取下一页的键集值
            next_values = None
            if has_next and items:
                next_values = [getattr(items[-1], field_name) for field_name, _ in sort_fields]

            # 创建分页元数据
            meta = PaginationMeta(
                page=1, size=per_page, has_next=has_next, next_cursor=next_values  # 键集分页不使用页码
            )

            return PaginationResult(items=items, meta=meta)
        except Exception as e:
            raise PaginationError(f"键集分页查询失败: {str(e)}")

    async def infinite_scroll(
        self,
        query: Union[Query, Select],
        timestamp_field: str = "create_time",
        last_timestamp: Optional[datetime] = None,
        size: int = 20,
    ) -> PaginationResult[Model]:
        """
        无限滚动分页查询
        :param query: 查询对象
        :param timestamp_field: 时间戳字段名
        :param last_timestamp: 上一页最后一条记录的时间戳
        :param size: 每页大小
        :return: 分页结果
        :raises PaginationError: 当无限滚动查询失败时
        """
        try:
            # 验证参数
            per_page = min(max(1, size), self.config.MAX_PER_PAGE)

            # 添加时间戳过滤
            if last_timestamp:
                model = query.column_descriptions[0]["type"]
                field = getattr(model, timestamp_field)
                query = query.filter(field < last_timestamp)

            # 添加排序
            query = query.order_by(desc(timestamp_field))

            # 获取数据
            items = await query.limit(per_page + 1).all()

            # 检查是否有下一页
            has_next = len(items) > per_page
            if has_next:
                items = items[:-1]

            # 获取下一页的时间戳
            next_timestamp = None
            if has_next and items:
                next_timestamp = getattr(items[-1], timestamp_field)

            # 创建分页元数据
            meta = PaginationMeta(
                page=1, size=per_page, has_next=has_next, next_cursor=next_timestamp  # 无限滚动不使用页码
            )

            return PaginationResult(items=items, meta=meta)
        except Exception as e:
            raise PaginationError(f"无限滚动查询失败: {str(e)}")


# 创建分页管理器实例
pagination_manager = PaginationManager()

# 导出
__all__ = [
    "pagination_manager",
    "PaginationError",
    "PageParams",
    "CursorParams",
    "PaginationResult",
    "PaginationMeta",
]
