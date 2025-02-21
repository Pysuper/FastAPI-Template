"""
数据库查询构建器模块
"""
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from sqlalchemy import Select, and_, desc, func, or_, select
from sqlalchemy.sql import Select as SelectType

from core.db.models.base import BaseModel
from core.db.session.manager import session_manager

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T", bound=BaseModel)


class QueryBuilder(Generic[T]):
    """查询构建器"""

    def __init__(self, model: Type[T]):
        self.model = model
        self.session_manager = session_manager
        self._query: SelectType = select(model)
        self._conditions = []
        self._order_by = []
        self._group_by = []
        self._limit = None
        self._offset = None
        self._joins = []

    def filter(self, *conditions) -> "QueryBuilder[T]":
        """添加AND条件"""
        self._conditions.extend(conditions)
        return self

    def filter_by(self, **kwargs) -> "QueryBuilder[T]":
        """按字段过滤"""
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                if isinstance(value, (list, tuple)):
                    self._conditions.append(getattr(self.model, key).in_(value))
                else:
                    self._conditions.append(getattr(self.model, key) == value)
        return self

    def filter_or(self, *conditions) -> "QueryBuilder[T]":
        """添加OR条件"""
        if conditions:
            self._conditions.append(or_(*conditions))
        return self

    def order_by(self, *criteria) -> "QueryBuilder[T]":
        """排序"""
        self._order_by.extend(criteria)
        return self

    def order_by_desc(self, *columns) -> "QueryBuilder[T]":
        """降序排序"""
        self._order_by.extend(desc(column) for column in columns)
        return self

    def group_by(self, *columns) -> "QueryBuilder[T]":
        """分组"""
        self._group_by.extend(columns)
        return self

    def limit(self, limit: int) -> "QueryBuilder[T]":
        """限制数量"""
        self._limit = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder[T]":
        """偏移量"""
        self._offset = offset
        return self

    def join(self, target, *props) -> "QueryBuilder[T]":
        """连接查询"""
        self._joins.append((target, props))
        return self

    def _build(self) -> Select:
        """构建查询"""
        query = self._query

        # 添加软删除过滤
        query = query.where(self.model.is_deleted == 0)

        # 添加条件
        if self._conditions:
            query = query.where(and_(*self._conditions))

        # 添加连接
        for target, props in self._joins:
            query = query.join(target, *props)

        # 添加分组
        if self._group_by:
            query = query.group_by(*self._group_by)

        # 添加排序
        if self._order_by:
            query = query.order_by(*self._order_by)

        # 添加分页
        if self._offset is not None:
            query = query.offset(self._offset)
        if self._limit is not None:
            query = query.limit(self._limit)

        return query

    async def count(self) -> int:
        """获取记录数量"""
        query = select(func.count()).select_from(self._build().subquery())
        return await self.session_manager.scalar(query)

    async def exists(self) -> bool:
        """检查是否存在"""
        return await self.count() > 0

    async def first(self) -> Optional[T]:
        """获取第一条记录"""
        query = self._build().limit(1)
        result = await self.session_manager.execute(query)
        return result.scalar_one_or_none()

    async def all(self) -> List[T]:
        """获取所有记录"""
        result = await self.session_manager.execute(self._build())
        return result.scalars().all()

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """分页查询"""
        # 计算总数
        total = await self.count()

        # 设置分页
        self.offset((page - 1) * page_size).limit(page_size)

        # 查询数据
        items = await self.all()

        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
        }

    async def scalar(self) -> Any:
        """获取标量结果"""
        result = await self.session_manager.execute(self._build())
        return result.scalar()

    async def update(self, values: Dict[str, Any]) -> int:
        """批量更新"""
        async with self.session_manager.transaction() as session:
            query = self._build()
            result = await session.execute(query.values(values))
            return result.rowcount

    async def delete(self) -> int:
        """批量删除"""
        async with self.session_manager.transaction() as session:
            query = self._build()
            result = await session.execute(query.values({"is_deleted": 1}))
            return result.rowcount 