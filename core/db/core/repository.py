"""
数据库仓储基类模块
"""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.sql import Select

from db.core.session import sync_db_manager

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """仓储基类"""

    def __init__(self, model: Type[T]):
        self.model = model
        self.session_manager = sync_db_manager

    async def get(self, id: int) -> Optional[T]:
        """根据ID获取记录"""
        return await self.session_manager.get(self.model, id)

    async def get_all(self) -> List[T]:
        """获取所有记录"""
        return await self.session_manager.get_all(self.model)

    async def create(self, data: Dict[str, Any]) -> T:
        """创建记录"""
        return await self.session_manager.create(self.model, data)

    async def update(self, instance: T, data: Dict[str, Any]) -> T:
        """更新记录"""
        return await self.session_manager.update(instance, data)

    async def delete(self, instance: T) -> None:
        """删除记录"""
        await self.session_manager.delete(instance)

    async def count(self, **filters) -> int:
        """获取记录数量"""
        query = select(func.count(self.model.id))
        query = self._apply_filters(query, **filters)
        return await self.session_manager.scalar(query)

    async def exists(self, **filters) -> bool:
        """检查记录是否存在"""
        return await self.count(**filters) > 0

    async def find_one(self, **filters) -> Optional[T]:
        """查找单条记录"""
        query = select(self.model)
        query = self._apply_filters(query, **filters)
        result = await self.session_manager.execute(query)
        return result.scalar_one_or_none()

    async def find_all(self, **filters) -> List[T]:
        """查找所有记录"""
        query = select(self.model)
        query = self._apply_filters(query, **filters)
        result = await self.session_manager.execute(query)
        return result.scalars().all()

    async def find_by_ids(self, ids: List[int]) -> List[T]:
        """根据ID列表查找记录"""
        query = select(self.model).where(
            self.model.id.in_(ids),
            self.model.is_deleted == 0,
        )
        result = await self.session_manager.execute(query)
        return result.scalars().all()

    def _apply_filters(self, query: Select, **filters) -> Select:
        """应用过滤条件"""
        # 添加软删除过滤
        query = query.where(self.model.is_deleted == 0)

        # 添加其他过滤条件
        for key, value in filters.items():
            if hasattr(self.model, key):
                if isinstance(value, (list, tuple)):
                    query = query.where(getattr(self.model, key).in_(value))
                else:
                    query = query.where(getattr(self.model, key) == value)

        return query

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 10,
        **filters,
    ) -> Dict[str, Any]:
        """分页查询"""
        # 计算总数
        total = await self.count(**filters)

        # 查询数据
        query = select(self.model)
        query = self._apply_filters(query, **filters)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session_manager.execute(query)
        items = result.scalars().all()

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
