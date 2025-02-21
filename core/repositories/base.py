"""
基础仓储模块
包含所有仓储类的基类，提供通用的CRUD操作和性能优化
"""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.cache.managers.manager import cache_manager
from core.db.core.base import AbstractModel
from core.schemas.base.pagination import PaginationParams
from core.strong.metrics import metrics_collector

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD操作的基础仓储类
    提供缓存支持和查询优化
    """

    def __init__(self, model: Type[ModelType]):
        """
        初始化
        :param model: SQLAlchemy模型类
        """
        self.model = model
        self.cache_prefix = f"{model.__tablename__}:"
        self.cache_ttl = timedelta(minutes=30)  # 默认缓存30分钟
        self._lock = asyncio.Lock()  # 并发控制锁

    def _build_cache_key(self, key: str, **kwargs: Any) -> str:
        """构建缓存键"""
        return cache_manager.build_key(self.cache_prefix, key, **kwargs)

    async def _execute_with_metrics(self, operation: str, func: callable, *args, **kwargs) -> Any:
        """
        执行数据库操作并记录指标
        """
        start_time = asyncio.get_event_loop().time()
        try:
            result = await func(*args, **kwargs)
            metrics_collector.track_database_query(
                database="main", operation=operation, duration=asyncio.get_event_loop().time() - start_time
            )
            return result
        except Exception as e:
            logger.error(f"Database operation failed: {operation}", exc_info=e)
            metrics_collector.increment("db_operation_errors_total", 1, {"operation": operation})
            raise

    async def get(
        self, db: AsyncSession, id: Any, *, for_update: bool = False, use_cache: bool = True
    ) -> Optional[ModelType]:
        """
        通过ID获取记录
        :param for_update: 是否使用SELECT FOR UPDATE
        :param use_cache: 是否使用缓存
        """
        try:
            if use_cache and not for_update:
                cache_key = self._build_cache_key("id", id=id)
                cached = await cache_manager.get(cache_key)
                if cached is not None:
                    metrics_collector.track_cache("repository", True)
                    return self.model(**cached)
                metrics_collector.track_cache("repository", False)

            async with db.begin():
                query = (
                    select(self.model)
                    .options(selectinload("*"))
                    .where(
                        self.model.id == id,
                        self.model.is_deleted == False,
                    )
                )

                if for_update:
                    query = query.with_for_update()

                result = await self._execute_with_metrics("get", db.execute, query)
                db_obj = result.scalar_one_or_none()

                if db_obj and use_cache and not for_update:
                    await cache_manager.set(cache_key, jsonable_encoder(db_obj), expire=self.cache_ttl)

                return db_obj

        except SQLAlchemyError as e:
            logger.error(f"Database error in get: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get: {e}", exc_info=True)
            raise

    async def get_multi(
        self, db: AsyncSession, *, pagination: PaginationParams, use_cache: bool = True, **filters: Any
    ) -> Tuple[List[ModelType], int]:
        """
        获取多条记录
        :param use_cache: 是否使用缓存
        """
        try:
            if use_cache:
                cache_key = self._build_cache_key("multi", page=pagination.page, size=pagination.size, **filters)
                cached = await cache_manager.get(cache_key)
                if cached is not None:
                    metrics_collector.track_cache("repository", True)
                    items = [self.model(**item) for item in cached["items"]]
                    return items, cached["total"]
                metrics_collector.track_cache("repository", False)

            async with db.begin():
                # 构建基础查询
                query = select(self.model).where(self.model.is_deleted == False)

                # 添加过滤条件
                for field, value in filters.items():
                    if value is not None:
                        query = query.where(getattr(self.model, field) == value)

                # 获取总数
                count_query = select(func.count()).select_from(query.subquery())
                total = await self._execute_with_metrics("count", db.scalar, count_query)

                # 优化大数据量查询
                if pagination.size > 100:
                    # 使用游标分页
                    query = (
                        query.order_by(self.model.id)
                        .options(selectinload("*"))
                        .offset((pagination.page - 1) * pagination.size)
                        .limit(pagination.size)
                    )
                else:
                    # 使用普通分页
                    query = (
                        query.options(selectinload("*"))
                        .offset((pagination.page - 1) * pagination.size)
                        .limit(pagination.size)
                    )

                # 执行查询
                result = await self._execute_with_metrics("get_multi", db.execute, query)
                items = result.scalars().all()

                if use_cache:
                    cache_data = {"items": [jsonable_encoder(item) for item in items], "total": total}
                    await cache_manager.set(cache_key, cache_data, expire=self.cache_ttl)

                return items, total

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_multi: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_multi: {e}", exc_info=True)
            raise

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType, use_cache: bool = True) -> ModelType:
        """创建记录"""
        async with self._lock:  # 使用锁保护创建操作
            try:
                async with db.begin():
                    obj_in_data = jsonable_encoder(obj_in)
                    db_obj = self.model(**obj_in_data)
                    db.add(db_obj)
                    await self._execute_with_metrics("create", db.commit)
                    await db.refresh(db_obj)

                    if use_cache:
                        cache_key = self._build_cache_key("id", id=db_obj.id)
                        await cache_manager.set(cache_key, jsonable_encoder(db_obj), expire=self.cache_ttl)

                    return db_obj

            except SQLAlchemyError as e:
                logger.error(f"Database error in create: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error in create: {e}", exc_info=True)
                raise

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        use_cache: bool = True,
    ) -> ModelType:
        """更新记录"""
        async with self._lock:  # 使用锁保护更新操作
            try:
                async with db.begin():
                    obj_data = jsonable_encoder(db_obj)
                    if isinstance(obj_in, dict):
                        update_data = obj_in
                    else:
                        update_data = obj_in.dict(exclude_unset=True)

                    for field in obj_data:
                        if field in update_data:
                            setattr(db_obj, field, update_data[field])

                    db.add(db_obj)
                    await self._execute_with_metrics("update", db.commit)
                    await db.refresh(db_obj)

                    if use_cache:
                        cache_key = self._build_cache_key("id", id=db_obj.id)
                        await cache_manager.set(cache_key, jsonable_encoder(db_obj), expire=self.cache_ttl)

                    return db_obj

            except SQLAlchemyError as e:
                logger.error(f"Database error in update: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error in update: {e}", exc_info=True)
                raise

    async def remove(self, db: AsyncSession, *, id: int, use_cache: bool = True) -> Optional[ModelType]:
        """删除记录（软删除）"""
        async with self._lock:  # 使用锁保护删除操作
            try:
                async with db.begin():
                    obj = await self.get(db, id=id, for_update=True)
                    if obj:
                        obj.is_deleted = True
                        db.add(obj)
                        await self._execute_with_metrics("remove", db.commit)

                        if use_cache:
                            cache_key = self._build_cache_key("id", id=id)
                            await cache_manager.delete(cache_key)

                    return obj

            except SQLAlchemyError as e:
                logger.error(f"Database error in remove: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error in remove: {e}", exc_info=True)
                raise

    async def bulk_create(
        self, db: AsyncSession, *, objs_in: List[CreateSchemaType], batch_size: int = 1000
    ) -> List[ModelType]:
        """批量创建记录"""
        async with self._lock:  # 使用锁保护批量创建操作
            try:
                created_objs = []
                for i in range(0, len(objs_in), batch_size):
                    batch = objs_in[i : i + batch_size]
                    async with db.begin():
                        db_objs = [self.model(**jsonable_encoder(obj)) for obj in batch]
                        db.add_all(db_objs)
                        await self._execute_with_metrics("bulk_create", db.commit)
                        for obj in db_objs:
                            await db.refresh(obj)
                        created_objs.extend(db_objs)
                return created_objs

            except SQLAlchemyError as e:
                logger.error(f"Database error in bulk_create: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error in bulk_create: {e}", exc_info=True)
                raise

    async def bulk_update(
        self,
        db: AsyncSession,
        *,
        objs: List[Tuple[ModelType, Union[UpdateSchemaType, Dict[str, Any]]]],
        batch_size: int = 1000,
    ) -> List[ModelType]:
        """批量更新记录"""
        async with self._lock:  # 使用锁保护批量更新操作
            try:
                updated_objs = []
                for i in range(0, len(objs), batch_size):
                    batch = objs[i : i + batch_size]
                    async with db.begin():
                        for db_obj, obj_in in batch:
                            if isinstance(obj_in, dict):
                                update_data = obj_in
                            else:
                                update_data = obj_in.dict(exclude_unset=True)
                            for field, value in update_data.items():
                                setattr(db_obj, field, value)
                            db.add(db_obj)
                        await self._execute_with_metrics("bulk_update", db.commit)
                        for db_obj, _ in batch:
                            await db.refresh(db_obj)
                            updated_objs.append(db_obj)
                return updated_objs

            except SQLAlchemyError as e:
                logger.error(f"Database error in bulk_update: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error in bulk_update: {e}", exc_info=True)
                raise

    async def execute_raw_sql(self, db: AsyncSession, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行原始SQL"""
        try:
            async with db.begin():
                result = await self._execute_with_metrics("raw_sql", db.execute, text(sql), params or {})
                return result

        except SQLAlchemyError as e:
            logger.error(f"Database error in execute_raw_sql: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in execute_raw_sql: {e}", exc_info=True)
            raise
