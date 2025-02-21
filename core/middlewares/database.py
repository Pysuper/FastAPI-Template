from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import desc, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from core.middlewares.exceptions import DatabaseException, ResourceNotFoundException

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """仓储基类"""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, schema: CreateSchemaType) -> ModelType:
        """创建记录"""
        try:
            data = schema.dict(exclude_unset=True)
            db_obj = self.model(**data)
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            return db_obj
        except Exception as e:
            await self.session.rollback()
            raise DatabaseException(f"Create error: {str(e)}")

    async def update(self, id: Any, schema: UpdateSchemaType) -> Optional[ModelType]:
        """更新记录"""
        try:
            data = schema.dict(exclude_unset=True)
            query = update(self.model).where(self.model.id == id).values(**data, updated_at=datetime.now())
            result = await self.session.execute(query)
            await self.session.commit()

            if result.rowcount == 0:
                raise ResourceNotFoundException(f"Record with id {id} not found")

            return await self.get(id)
        except ResourceNotFoundException:
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseException(f"Update error: {str(e)}")

    async def delete(self, id: Any) -> bool:
        """删除记录"""
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            await self.session.commit()

            if result.rowcount == 0:
                raise ResourceNotFoundException(f"Record with id {id} not found")

            return True
        except ResourceNotFoundException:
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseException(f"Delete error: {str(e)}")

    async def get(self, id: Any) -> Optional[ModelType]:
        """获取单条记录"""
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseException(f"Get error: {str(e)}")

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """获取多条记录"""
        try:
            query = select(self.model)

            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.where(getattr(self.model, field) == value)

            query = query.offset(skip).limit(limit)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseException(f"Get multi error: {str(e)}")

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """获取记录总数"""
        try:
            query = select(self.model)

            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        query = query.where(getattr(self.model, field) == value)

            result = await self.session.execute(select(func.count()).select_from(query.subquery()))
            return result.scalar_one()
        except Exception as e:
            raise DatabaseException(f"Count error: {str(e)}")

    def _apply_ordering(self, query: Select, ordering: Optional[Dict[str, str]] = None) -> Select:
        """应用排序"""
        if ordering:
            for field, direction in ordering.items():
                if hasattr(self.model, field):
                    if direction.lower() == "desc":
                        query = query.order_by(desc(getattr(self.model, field)))
                    else:
                        query = query.order_by(getattr(self.model, field))
        return query

    def _apply_filters(self, query: Select, filters: Optional[Dict[str, Any]] = None) -> Select:
        """应用过滤"""
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, (list, tuple)):
                        query = query.where(getattr(self.model, field).in_(value))
                    elif isinstance(value, dict):
                        operator = value.get("operator")
                        if operator == "like":
                            query = query.where(getattr(self.model, field).like(f"%{value['value']}%"))
                        elif operator == "gt":
                            query = query.where(getattr(self.model, field) > value["value"])
                        elif operator == "lt":
                            query = query.where(getattr(self.model, field) < value["value"])
                        elif operator == "gte":
                            query = query.where(getattr(self.model, field) >= value["value"])
                        elif operator == "lte":
                            query = query.where(getattr(self.model, field) <= value["value"])
                    else:
                        query = query.where(getattr(self.model, field) == value)
        return query


class BaseSyncRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """同步仓储基类"""

    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session

    def create(self, schema: CreateSchemaType) -> ModelType:
        """创建记录"""
        try:
            data = schema.dict(exclude_unset=True)
            db_obj = self.model(**data)
            self.session.add(db_obj)
            self.session.commit()
            self.session.refresh(db_obj)
            return db_obj
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Create error: {str(e)}")

    def update(self, id: Any, schema: UpdateSchemaType) -> Optional[ModelType]:
        """更新记录"""
        try:
            data = schema.dict(exclude_unset=True)
            query = update(self.model).where(self.model.id == id).values(**data, updated_at=datetime.now())
            result = self.session.execute(query)
            self.session.commit()

            if result.rowcount == 0:
                raise ResourceNotFoundException(f"Record with id {id} not found")

            return self.get(id)
        except ResourceNotFoundException:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Update error: {str(e)}")

    def delete(self, id: Any) -> bool:
        """删除记录"""
        try:
            query = delete(self.model).where(self.model.id == id)
            result = self.session.execute(query)
            self.session.commit()

            if result.rowcount == 0:
                raise ResourceNotFoundException(f"Record with id {id} not found")

            return True
        except ResourceNotFoundException:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Delete error: {str(e)}")

    def get(self, id: Any) -> Optional[ModelType]:
        """获取单条记录"""
        try:
            return self.session.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            raise DatabaseException(f"Get error: {str(e)}")

    def get_multi(
        self, *, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """获取多条记录"""
        try:
            query = self.session.query(self.model)
            query = self._apply_filters(query, filters)
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Get multi error: {str(e)}")

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """获取记录总数"""
        try:
            query = self.session.query(self.model)
            query = self._apply_filters(query, filters)
            return query.count()
        except Exception as e:
            raise DatabaseException(f"Count error: {str(e)}")

    def _apply_filters(self, query: Query, filters: Optional[Dict[str, Any]] = None) -> Query:
        """应用过滤"""
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, (list, tuple)):
                        query = query.filter(getattr(self.model, field).in_(value))
                    elif isinstance(value, dict):
                        operator = value.get("operator")
                        if operator == "like":
                            query = query.filter(getattr(self.model, field).like(f"%{value['value']}%"))
                        elif operator == "gt":
                            query = query.filter(getattr(self.model, field) > value["value"])
                        elif operator == "lt":
                            query = query.filter(getattr(self.model, field) < value["value"])
                        elif operator == "gte":
                            query = query.filter(getattr(self.model, field) >= value["value"])
                        elif operator == "lte":
                            query = query.filter(getattr(self.model, field) <= value["value"])
                    else:
                        query = query.filter(getattr(self.model, field) == value)
        return query
