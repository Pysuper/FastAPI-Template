from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from core.db.core.base import DBBase
from db.metrics.pagination import PaginationParams

ModelType = TypeVar("ModelType", bound=DBBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """增强的CRUD基础类"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any, for_update: bool = False) -> Optional[ModelType]:
        """获取单个对象
        Args:
            db: 数据库会话
            id: 对象ID
            for_update: 是否加锁
        """
        query = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        if for_update:
            query = query.with_for_update()
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        pagination: PaginationParams,
        filters: Dict[str, Any] = None,
        order_by: List[str] = None,
    ) -> tuple[List[ModelType], int]:
        """获取多个对象
        Args:
            pagination: 分页参数
            filters: 过滤条件
            order_by: 排序字段
        """
        filters = filters or {}
        query = select(self.model).where(self.model.is_deleted == False)

        # 应用过滤条件
        for field, value in filters.items():
            if value is not None:
                query = query.where(getattr(self.model, field) == value)

        # 应用排序
        if order_by:
            for field in order_by:
                if field.startswith("-"):
                    query = query.order_by(getattr(self.model, field[1:]).desc())
                else:
                    query = query.order_by(getattr(self.model, field).asc())

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # 分页
        query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)
        result = await db.execute(query)
        return result.scalars().all(), total

    async def create(self, db: AsyncSession, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """创建对象"""
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = jsonable_encoder(obj_in)

        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def bulk_create(
        self, db: AsyncSession, *, objs_in: List[Union[CreateSchemaType, Dict[str, Any]]]
    ) -> List[ModelType]:
        """批量创建对象"""
        db_objs = []
        for obj_in in objs_in:
            if isinstance(obj_in, dict):
                obj_in_data = obj_in
            else:
                obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)

        db.add_all(db_objs)
        await db.commit()
        for obj in db_objs:
            await db.refresh(obj)
        return db_objs

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        version: Optional[int] = None,
    ) -> ModelType:
        """更新对象（支持乐观锁）"""
        if version is not None and db_obj.version != version:
            raise StaleDataError("数据已被修改，请刷新后重试")

        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def bulk_update(
        self, db: AsyncSession, *, objs: List[tuple[ModelType, Union[UpdateSchemaType, Dict[str, Any]]]]
    ) -> List[ModelType]:
        """批量更新对象"""
        updated_objs = []
        for db_obj, obj_in in objs:
            updated_obj = await self.update(db=db, db_obj=db_obj, obj_in=obj_in)
            updated_objs.append(updated_obj)
        return updated_objs

    async def remove(self, db: AsyncSession, *, id: int, force: bool = False) -> ModelType:
        """删除对象
        Args:
            force: 是否强制删除（硬删除）
        """
        obj = await self.get(db=db, id=id)
        if obj:
            if force:
                await db.delete(obj)
            else:
                obj.soft_delete()
            await db.commit()
        return obj

    async def bulk_remove(self, db: AsyncSession, *, ids: List[int], force: bool = False) -> List[ModelType]:
        """批量删除对象"""
        objs = []
        for id in ids:
            obj = await self.remove(db=db, id=id, force=force)
            if obj:
                objs.append(obj)
        return objs

    async def count(self, db: AsyncSession, filters: dict = None) -> int:
        """统计记录数"""
        query = db.query(self.model).filter(self.model.is_delete == False)
        if filters:
            for k, v in filters.items():
                if hasattr(self.model, k):
                    query = query.filter(getattr(self.model, k) == v)
        return query.count()

    async def exists(self, db: AsyncSession, id: int) -> bool:
        """检查记录是否存在"""
        return (
            await db.scalar(
                select(func.count()).where(
                    self.model.id == id,
                    self.model.is_delete == False,
                ),
            )
            > 0
        )

    # 软删除
    async def soft_delete(
        self,
        db: AsyncSession,
        *,
        id: int,
        deleter_id: int = None,
        deleter_name: str = None,
    ) -> ModelType:
        """软删除"""
        obj = await self.get(db=db, id=id)
        if obj:
            obj.is_delete = True
            obj.delete_time = datetime.now()
            if deleter_id:
                obj.delete_by = deleter_id
                obj.delete_by_name = deleter_name
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
        return obj

    async def hard_delete(self, db: AsyncSession, *, id: int) -> ModelType:
        """硬删除"""
        obj = await self.get(db=db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
            await db.refresh(obj)
        return obj
