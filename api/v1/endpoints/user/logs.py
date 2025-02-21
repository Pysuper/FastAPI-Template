from typing import Optional, Any

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from api.base.crud import CRUDRouter
from api.v1.endpoints.system.logs import Log, LogCreate, LogUpdate, LogFilter
from core.dependencies import async_db
from schemas.base.response import Response
from services.system.log_service import LogService

# 创建路由器
router = CRUDRouter(
    schema=Log,
    create_schema=LogCreate,
    update_schema=LogUpdate,
    service=LogService(),
    prefix="/logs",
    tags=["日志管理"],
)

# 设置路由前缀和标签
router.router.prefix = "/logs"
router.router.tags = ["日志管理"]


@router.router.get("/types", response_model=Response, summary="获取日志类型列表")
async def get_log_types(db: Session = Depends(async_db)):
    """获取日志类型列表"""

    return Response(data=[])


@router.router.get("/levels", response_model=Response, summary="获取日志级别列表")
async def get_log_levels(db: Session = Depends(async_db)):
    """获取日志级别列表"""

    return Response(data=[])


@router.router.get("/modules", response_model=Response, summary="获取日志模块列表")
async def get_log_modules(db: Session = Depends(async_db)):
    """获取日志模块列表"""

    return Response(data=[])


@router.router.get("/users", response_model=Response, summary="获取日志用户列表")
async def get_log_users(db: Session = Depends(async_db)):
    """获取日志用户列表"""

    return Response(data=[])


@router.router.get("/operations", response_model=Response, summary="获取日志操��列表")
async def get_log_operations(db: Session = Depends(async_db)):
    """获取日志操作列表"""

    return Response(data=[])


@router.router.get("/search", response_model=Response, summary="搜索日志")
async def search_logs(
    keyword: str = Query(None, description="搜索关键词"),
    log_type: str = Query(None, description="日志类型"),
    level: str = Query(None, description="日志级别"),
    module: str = Query(None, description="日志模块"),
    user_id: int = Query(None, description="用户ID"),
    operation: str = Query(None, description="操作类型"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(async_db),
):
    """搜索日志"""

    return Response(data=[])


@router.router.get("/stats", response_model=Response, summary="获取日志统计")
async def get_log_stats(
    log_type: str = Query(None, description="日志类型"),
    level: str = Query(None, description="日志级别"),
    module: str = Query(None, description="日志��块"),
    user_id: int = Query(None, description="用户ID"),
    operation: str = Query(None, description="操作类型"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
):
    """获取日志统计"""

    return Response(data={})


async def log_operation(
    db: Session,
    module: str,
    action: str,
    user_id: int,
    target: Optional[Any] = None,
    status: str = "success",
    detail: Optional[dict] = None,
    request: Optional[Request] = None,
):
    """记录操作日志"""
    log = {
        "module": module,
        "type": "operation",
        "title": f"{action}",
        "content": str(detail) if detail else None,
        "user_id": user_id,
        "status": status,
        "target_type": target.__class__.__name__ if target else None,
        "target_id": str(target.id) if target and hasattr(target, "id") else None,
    }

    # 如果有请求信息
    if request:
        log.update(
            {
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "method": request.method,
                "url": str(request.url),
                "params": str(request.query_params),
            }
        )

    # 创建日志记录
    db_log = Log(**log)
    db.add(db_log)
    db.commit()


async def log_error(
    db: Session,
    module: str,
    action: str,
    error: Exception,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
):
    """记录错误日志"""
    log = {
        "module": module,
        "type": "error",
        "title": f"{action}失败",
        "content": str(error),
        "error": str(error),
        "user_id": user_id,
        "status": "error",
    }

    # 如果有请求信息
    if request:
        log.update(
            {
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "method": request.method,
                "url": str(request.url),
                "params": str(request.query_params),
            }
        )

    # 创建日志记录
    db_log = Log(**log)
    db.add(db_log)
    db.commit()


async def log_login(db: Session, user_id: int, status: str, ip: str, user_agent: str):
    """记录登录日志"""
    log = {
        "module": "认证",
        "type": "login",
        "title": "用户登录",
        "user_id": user_id,
        "status": status,
        "ip": ip,
        "user_agent": user_agent,
    }

    # 创建日志记录
    db_log = Log(**log)
    db.add(db_log)
    db.commit()


# 日志装饰器
def operation_log(module: str, action: str):
    """操作日志装饰器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取数据库会话
            db = next(get_db())
            # 获取当前用户
            current_user = kwargs.get("current_user")
            # 获取请求对象
            request = kwargs.get("request")

            try:
                # 执行原函数
                result = await func(*args, **kwargs)

                # 记录操作日志
                await log_operation(
                    db=db,
                    module=module,
                    action=action,
                    user_id=current_user,
                    target=result.get("data") if isinstance(result, dict) else None,
                    status="success",
                    request=request,
                )

                return result

            except Exception as e:
                # 记录错误日志
                await log_error(db=db, module=module, action=action, error=e, user_id=current_user, request=request)
                raise

        return wrapper

    return decorator


# 使用示例:
"""
@router.post("/users")
@operation_log(module="用户管理", action="创建用户")
async def create_user(
    user: UserCreate,
    request: Request,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user)
):
    # 创建用户的业务逻辑
    pass
"""
