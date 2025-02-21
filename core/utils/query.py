from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Query, Session

from core.cache.decorators import cache


class QueryOptimizer:
    """查询优化工具类"""

    @staticmethod
    def paginate(query: Query, page: int = 1, page_size: int = 10, max_page_size: int = 100) -> tuple:
        """分页查询
        Args:
            query: 查询对象
            page: 页码
            page_size: 每页数量
            max_page_size: 最大每页数量
        Returns:
            tuple: (数据列表, 总数)
        """
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > max_page_size:
            page_size = max_page_size

        # 计算总数
        total = query.count()

        # 分页查询
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    @staticmethod
    def build_filters(query: Query, model: Type[BaseModel], filters: Dict[str, Any]) -> Query:
        """构建过滤条件
        Args:
            query: 查询对象
            model: 模型类
            filters: 过滤条件
        Returns:
            Query: 查询对象
        """
        for field, value in filters.items():
            if value is not None:
                if isinstance(value, (list, tuple)):
                    query = query.filter(getattr(model, field).in_(value))
                elif isinstance(value, dict):
                    for op, val in value.items():
                        if op == "eq":
                            query = query.filter(getattr(model, field) == val)
                        elif op == "ne":
                            query = query.filter(getattr(model, field) != val)
                        elif op == "gt":
                            query = query.filter(getattr(model, field) > val)
                        elif op == "gte":
                            query = query.filter(getattr(model, field) >= val)
                        elif op == "lt":
                            query = query.filter(getattr(model, field) < val)
                        elif op == "lte":
                            query = query.filter(getattr(model, field) <= val)
                        elif op == "like":
                            query = query.filter(getattr(model, field).like(f"%{val}%"))
                        elif op == "ilike":
                            query = query.filter(getattr(model, field).ilike(f"%{val}%"))
                        elif op == "in":
                            query = query.filter(getattr(model, field).in_(val))
                        elif op == "not_in":
                            query = query.filter(~getattr(model, field).in_(val))
                        elif op == "is_null":
                            if val:
                                query = query.filter(getattr(model, field).is_(None))
                            else:
                                query = query.filter(getattr(model, field).isnot(None))
                else:
                    query = query.filter(getattr(model, field) == value)
        return query

    @staticmethod
    def build_order_by(query: Query, model: Type[BaseModel], order_by: List[str]) -> Query:
        """构建排序条件
        Args:
            query: 查询对象
            model: 模型类
            order_by: 排序字段列表,如: ["id desc", "name asc"]
        Returns:
            Query: 查询对象
        """
        if order_by:
            for field in order_by:
                if " " in field:
                    field, direction = field.split(" ")
                    if direction.lower() == "desc":
                        query = query.order_by(getattr(model, field).desc())
                    else:
                        query = query.order_by(getattr(model, field).asc())
                else:
                    query = query.order_by(getattr(model, field).asc())
        return query

    @staticmethod
    def build_query(
        db: Session,
        model: Type[BaseModel],
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        max_page_size: int = 100,
        select_columns: Optional[List[str]] = None,
        join_models: Optional[List[Type[BaseModel]]] = None,
        cache_key: Optional[str] = None,
        cache_expire: Optional[int] = None,
    ) -> Union[tuple, List[BaseModel]]:
        """构建查询
        Args:
            db: 数据库会话
            model: 模型类
            filters: 过滤条件
            order_by: 排序字段列表
            page: 页码
            page_size: 每页数量
            max_page_size: 最大每页数量
            select_columns: 查询字段列表
            join_models: 关联模型列表
            cache_key: 缓存键
            cache_expire: 缓存过期时间(秒)
        Returns:
            Union[tuple, List[BaseModel]]: 如果分页则返回(数据列表,总数),否则返回数据列表
        """
        # 检查缓存
        if cache_key:
            cached_data = cache.get_object(cache_key)
            if cached_data is not None:
                return cached_data

        # 构建查询
        if select_columns:
            query = db.query(*[getattr(model, col) for col in select_columns])
        else:
            query = db.query(model)

        # 关联查询
        if join_models:
            for join_model in join_models:
                query = query.join(join_model)

        # 过滤条件
        if filters:
            query = QueryOptimizer.build_filters(query, model, filters)

        # 排序
        if order_by:
            query = QueryOptimizer.build_order_by(query, model, order_by)

        # 分页查询
        if page is not None and page_size is not None:
            result = QueryOptimizer.paginate(query, page, page_size, max_page_size)
        else:
            result = query.all()

        # 设置缓存
        if cache_key:
            cache.set_object(cache_key, result, cache_expire)

        return result

    @staticmethod
    def execute_raw_sql(
        db: Session,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        cache_expire: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """执行原生SQL
        Args:
            db: 数据库会话
            sql: SQL语句
            params: SQL参数
            cache_key: 缓存键
            cache_expire: 缓存过期时间(秒)
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        # 检查缓存
        if cache_key:
            cached_data = cache.get_object(cache_key)
            if cached_data is not None:
                return cached_data

        # 执行查询
        result = db.execute(text(sql), params or {})
        data = [dict(row) for row in result]

        # 设置缓存
        if cache_key:
            cache.set_object(cache_key, data, cache_expire)

        return data
