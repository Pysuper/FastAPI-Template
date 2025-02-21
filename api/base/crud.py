"""
增强的 CRUD 路由基类

特性:
    1. 完整的 CRUD 操作支持
    2. 批量操作能力
    3. 导入导出功能
    4. 数据统计分析
    5. 缓存支持
    6. 事件钩子
    7. 自定义过滤
    8. 权限控制
    9. 响应格式化
    10. 错误处理

使用示例:
    ```python
    class UserRouter(CRUDRouter[User, UserCreate, UserUpdate, UserFilter, UserResponse]):
        def __init__(self):
            super().__init__(
                schema=UserResponse,
                create_schema=UserCreate,
                update_schema=UserUpdate,
                filter_schema=UserFilter,
                service=UserService(),
                prefix="/users",
                tags=["用户管理"]
            )
    ```
"""

from datetime import date
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    cast,
)

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from core.cache.decorators import cache
from db.metrics.pagination import PageResponse
from dependencies import sync_db
from schemas.base.response import Response
from schemas.responses.files import ExportResponse, ImportResponse
from schemas.responses.stats import StatsResponse

# 类型变量定义
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
FilterSchemaType = TypeVar("FilterSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class CRUDRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType, FilterSchemaType, ResponseSchemaType]):
    """
    CRUD 路由基类

    提供了一个强大的、可扩展的 CRUD 路由基类，支持：
        1. 标准的 CRUD 操作
        2. 批量操作支持
        3. 导入/导出功能
        4. 统计分析
        5. 自定义过滤
        6. 缓存支持
        7. 事件钩子
        8. 权限控制
    """

    @staticmethod
    def default_generate_unique_id(route: APIRoute) -> str:
        """生成路由唯一ID的默认实现"""
        tag = route.tags[0] if route.tags else ""
        return f"{tag}_{route.name}_{route.path}"

    def __init__(
        self,
        *,
        schema: Type[ResponseSchemaType],
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        filter_schema: Optional[Type[FilterSchemaType]] = None,
        service: Any = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[Depends]] = None,
        cache_config: Optional[Dict[str, Any]] = None,
        generate_unique_id_function: Optional[Callable] = None,
    ):
        """
        初始化 CRUD 路由

        Args:
            schema: 响应模型类
            create_schema: 创建模型类
            update_schema: 更新模型类
            filter_schema: 过滤模型类
            service: 服务实例
            prefix: 路由前缀
            tags: 路由标签
            dependencies: 路由依赖
            cache_config: 缓存配置
            generate_unique_id_function: 生成唯一ID的函数
        """
        self.schema = schema
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.filter_schema = filter_schema
        self.service = service
        self.router = APIRouter(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies or [],
            generate_unique_id_function=generate_unique_id_function or self.default_generate_unique_id,
        )

        # TODO: 初始化缓存管理器
        # if cache_config:
        #     self.cache_manager = CacheManager(**cache_config)
        #     asyncio.create_task(self.cache_manager.init(CacheConfig()))
        # else:
        #     self.cache_manager = None

        self.generate_unique_id_function = generate_unique_id_function or self.default_generate_unique_id

        # 注册路由
        self._register_routes()
        self._register_batch_routes()
        self._register_extra_routes()

    def _register_routes(self) -> None:
        """注册基本 CRUD 路由"""

        @self.router.get(
            "/",
            response_model=PageResponse[self.schema],
            summary="获取列表",
            description="获取分页列表数据，支持搜索、排序和过滤",
        )
        @cache(key_prefix="student-get-list:", ttl=300, key_builder=lambda q, p, s, f: f"list:{q}:{p}:{s}:{f}")
        async def list_items(
            query: Optional[str] = Query(None, description="搜索关键词"),
            page: int = Query(1, ge=1, description="页码"),
            size: int = Query(20, ge=1, le=100, description="每页数量"),
            sort: Optional[str] = Query(None, description="排序字段"),
            filter_data: Optional[FilterSchemaType] = None,
            db: Session = Depends(self.get_db),
        ) -> PageResponse[ResponseSchemaType]:
            """获取列表数据

            支持:
            1. 关键词搜索
            2. 分页查询
            3. 字段排序
            4. 条件过滤
            5. 缓存支持
            """
            try:
                total, items = await self.service.get_list(
                    db=db,
                    query=query,
                    page=page,
                    size=size,
                    sort=sort,
                    filter_data=filter_data,
                )
                return PageResponse(total=total, items=items, page=page, size=size)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.post(
            "/",
            response_model=self.schema,
            summary="创建",
            description="创建新记录",
        )
        async def create_item(
            item: CreateSchemaType,
            db: Session = Depends(self.get_db),
        ) -> ResponseSchemaType:
            """创建新记录

            支持:
            1. 数据验证
            2. 业务规则检查
            3. 关联数据处理
            4. 事件通知
            """
            try:
                return await self.service.create(db=db, data=item)
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.get(
            "/{id}",
            response_model=self.schema,
            summary="获取详情",
            description="获取单条记录详情",
        )
        @cache(key_prefix="student-get-detail:", ttl=300, key_builder=lambda id: f"detail:{id}")
        async def get_item(
            id: int = Path(..., description="记录ID"),
            db: Session = Depends(self.get_db),
        ) -> ResponseSchemaType:
            """获取记录详情

            支持:
            1. 缓存
            2. 关联数据
            3. 权限检查
            """
            try:
                item = await self.service.get(db=db, id=id)
                if not item:
                    raise HTTPException(status_code=404, detail="记录不存在")
                return item
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.put(
            "/{id}",
            response_model=self.schema,
            summary="更新",
            description="更新现有记录",
        )
        async def update_item(
            id: int = Path(..., description="记录ID"),
            item: UpdateSchemaType = Body(..., description="更新数据"),
            db: Session = Depends(self.get_db),
        ) -> ResponseSchemaType:
            """更新记录

            支持:
            1. 部分更新
            2. 数据验证
            3. 业务规则检查
            4. 关联数据处理
            5. 缓存更新
            6. 事件通知
            """
            try:
                updated = await self.service.update(db=db, id=id, data=item)
                if not updated:
                    raise HTTPException(status_code=404, detail="记录不存在")
                # 清除缓存
                if self.cache_manager:
                    await self.cache_manager.delete(f"detail:{id}")
                    await self.cache_manager.delete_pattern("list:*")
                return updated
            except HTTPException:
                raise
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.delete(
            "/{id}",
            response_model=Response,
            summary="删除",
            description="删除现有记录",
        )
        async def delete_item(
            id: int = Path(..., description="记录ID"),
            db: Session = Depends(self.get_db),
        ) -> Response:
            """删除记录

            支持:
            1. 软删除
            2. 关联数据处理
            3. 缓存清理
            4. 事件通知
            """
            try:
                await self.service.delete(db=db, id=id)
                # 清除缓存
                if self.cache_manager:
                    await self.cache_manager.delete(f"detail:{id}")
                    await self.cache_manager.delete_pattern("list:*")
                return Response(message="删除成功")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    def _register_batch_routes(self) -> None:
        """注册批量操作路由"""

        @self.router.post(
            "/batch",
            response_model=List[self.schema],
            summary="批量创建",
            description="批量创建多条记录",
        )
        async def batch_create(
            items: List[CreateSchemaType],
            db: Session = Depends(self.get_db),
        ) -> List[ResponseSchemaType]:
            """批量创建记录

            支持:
            1. 事务处理
            2. 数据验证
            3. 业务规则检查
            4. 批量插入优化
            """
            try:
                return await self.service.batch_create(db=db, items=items)
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.put(
            "/batch",
            response_model=List[self.schema],
            summary="批量更新",
            description="批量更新多条记录",
        )
        async def batch_update(
            items: List[UpdateSchemaType],
            db: Session = Depends(self.get_db),
        ) -> List[ResponseSchemaType]:
            """批量更新记录

            支持:
            1. 事务处理
            2. 数据验证
            3. 业务规则检查
            4. 批量更新优化
            5. 缓存更新
            """
            try:
                updated = await self.service.batch_update(db=db, items=items)
                # 清除缓存
                if self.cache_manager:
                    for item in updated:
                        await self.cache_manager.delete(f"detail:{item.id}")
                    await self.cache_manager.delete_pattern("list:*")
                return updated
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.delete(
            "/batch",
            response_model=Response,
            summary="批量删除",
            description="批量删除多条记录",
        )
        async def batch_delete(
            ids: List[int] = Body(..., description="ID列表"),
            db: Session = Depends(self.get_db),
        ) -> Response:
            """批量删除记录

            支持:
            1. 事务处理
            2. 关联数据处理
            3. 批量删除优化
            4. 缓存清理
            """
            try:
                await self.service.batch_delete(db=db, ids=ids)
                # 清除缓存
                if self.cache_manager:
                    for id in ids:
                        await self.cache_manager.delete(f"detail:{id}")
                    await self.cache_manager.delete_pattern("list:*")
                return Response(message="批量删除成功")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    def _register_extra_routes(self) -> None:
        """注册扩展功能路由"""

        @self.router.post(
            "/import",
            response_model=ImportResponse,
            summary="导入数据",
            description="从文件导入数据",
        )
        async def import_data(
            file: UploadFile = File(...),
            db: Session = Depends(self.get_db),
        ) -> ImportResponse:
            """导入数据

            支持:
            1. 多种文件格式
            2. 数据验证
            3. 错误处理
            4. 导入进度
            5. 结果报告
            """
            try:
                result = await self.service.import_data(db=db, file=file)
                # 清除缓存
                if self.cache_manager:
                    await self.cache_manager.delete_pattern("list:*")
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.get(
            "/export",
            response_model=ExportResponse,
            summary="导出数据",
            description="导出数据到文件",
        )
        async def export_data(
            query: Optional[str] = Query(None, description="搜索关键词"),
            filter_data: Optional[FilterSchemaType] = None,
            db: Session = Depends(self.get_db),
        ) -> ExportResponse:
            """导出数据

            支持:
            1. 多种文件格式
            2. 数据过滤
            3. 自定义字段
            4. 大数据处理
            5. 异步导出
            """
            try:
                return await self.service.export_data(db=db, query=query, filter_data=filter_data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.router.get(
            "/stats",
            response_model=StatsResponse,
            summary="统计分析",
            description="获取数据统计信息",
        )
        @cache(key_prefix="student-get-stats:", ttl=300)
        async def get_stats(
            group_by: Optional[str] = Query(None, description="分组字段"),
            start_date: Optional[date] = Query(None, description="开始日期"),
            end_date: Optional[date] = Query(None, description="结束日期"),
            filter_data: Optional[FilterSchemaType] = None,
            db: Session = Depends(self.get_db),
        ) -> StatsResponse:
            """获取统计数据

            支持:
            1. 多维分析
            2. 时间范围
            3. 数据过滤
            4. 缓存支持
            5. 图表数据
            """
            try:
                return await self.service.get_stats(
                    db=db, group_by=group_by, start_date=start_date, end_date=end_date, filter_data=filter_data
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    def get_db(self) -> Session:
        """获取数据库会话"""
        return next(sync_db())

    @property
    def routes(self) -> List[APIRoute]:
        """获取路由列表"""
        return self.router.routes

    @property
    def dependencies(self) -> List[Depends]:
        """获取路由依赖"""
        return cast(List[Depends], self.router.dependencies)

    @property
    def default_response_class(self) -> Type[Response]:
        """获取默认响应类"""
        return cast(Type[Response], self.router.default_response_class or JSONResponse)

    @property
    def route_class(self) -> Type[APIRoute]:
        """获取路由类"""
        return cast(Type[APIRoute], self.router.route_class or APIRoute)

    @property
    def on_startup(self) -> Sequence[Callable]:
        """获取启动事件处理器"""
        return self.router.on_startup

    @property
    def on_shutdown(self) -> Sequence[Callable]:
        """获取关闭事件处理器"""
        return self.router.on_shutdown


class NotFoundError:
    pass
