# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：base.py
@Author  ：PySuper
@Date    ：2025/1/2 11:29 
@Desc    ：Speedy base.py
"""

"""
服务基类模块

提供服务层通用功能和基础设施
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 定义泛型类型变量
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用服务基类

    提供标准的CRUD操作实现

    泛型参数:
        ModelType: SQLAlchemy模型类型
        CreateSchemaType: 创建对象的Pydantic模型类型
        UpdateSchemaType: 更新对象的Pydantic模型类型
    """

    def __init__(self, model: Type[ModelType]):
        """
        初始化服务

        Args:
            model: SQLAlchemy模型类
        """
        self.model = model

    async def get(
        self,
        session: AsyncSession,
        id: Any,
    ) -> Optional[ModelType]:
        """
        根据ID获取单个对象

        Args:
            session: 数据库会话
            id: 对象ID

        Returns:
            查询到的对象，如果不存在则返回None

        Raises:
            NotFoundException: 对象不存在时抛出
        """
        query = select(self.model).filter(self.model.id == id)
        result = await session.execute(query)
        obj = result.scalar_one_or_none()

        if obj is None:
            raise NotFoundException(f"{self.model.__name__}不存在")

        return obj

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        获取多个对象

        Args:
            session: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数限制
            filters: 过滤条件

        Returns:
            对象列表
        """
        query = select(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    async def create(
        self,
        session: AsyncSession,
        obj_in: CreateSchemaType,
    ) -> ModelType:
        """
        创建新对象

        Args:
            session: 数据库会话
            obj_in: 创建对象的数据

        Returns:
            创建的对象

        Raises:
            ValidationException: 数据验证失败时抛出
        """
        try:
            obj_data = obj_in.dict(exclude_unset=True)
            db_obj = self.model(**obj_data)
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except Exception as e:
            await session.rollback()
            raise ValidationException(str(e))

    async def update(
        self,
        session: AsyncSession,
        *,
        id: Any,
        obj_in: UpdateSchemaType,
    ) -> ModelType:
        """
        更新对象

        Args:
            session: 数据库会话
            id: 对象ID
            obj_in: 更新的数据

        Returns:
            更新后的对象

        Raises:
            NotFoundException: 对象不存在时抛出
            ValidationException: 数据验证失败时抛出
        """
        try:
            db_obj = await self.get(session, id)
            update_data = obj_in.dict(exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_obj, field, value)

            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except NotFoundException:
            raise
        except Exception as e:
            await session.rollback()
            raise ValidationException(str(e))

    async def delete(
        self,
        session: AsyncSession,
        *,
        id: Any,
    ) -> ModelType:
        """
        删除对象

        Args:
            session: 数据库会话
            id: 对象ID

        Returns:
            被删除的对象

        Raises:
            NotFoundException: 对象不存在时抛出
        """
        obj = await self.get(session, id)
        await session.delete(obj)
        await session.commit()
        return obj
