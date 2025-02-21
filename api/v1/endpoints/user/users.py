from io import BytesIO
from typing import List, Any, Dict

from fastapi import APIRouter, Depends, Query, Path, Body, File, status
from fastapi import UploadFile as FastAPIUploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.metrics.pagination import PageResponse
from core.dependencies.auth import get_current_active_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from schemas.validators.rbac import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
    UserPermissionUpdate,
)

from models.user import User
from core.services.user import UserService

router = APIRouter()


@router.get("/", response_model=PageResponse[UserResponse], summary="获取用户列表")
async def get_users(
    query: str = Query(None, description="搜索关键词"),
    role: str = Query(None, description="角色"),
    status: str = Query(None, description="状态"),
    department_id: int = Query(None, description="部门ID"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query(None, description="排序字段"),
    order: str = Query("desc", description="排序方向"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户列表"""
    service = UserService(db)
    total, items = service.get_users(
        query=query,
        role=role,
        status=status,
        department_id=department_id,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
        sort=sort,
        order=order,
    )
    return PageResponse(total=total, items=items, page=page, size=size)


class UserStatsResponse(BaseModel):
    """用户统计响应模型"""

    total_users: int = 0
    active_users: int = 0
    inactive_users: int = 0
    today_logins: int = 0
    details: Dict[str, Any] = {}


class RoleListResponse(BaseModel):
    """角色列表响应模型"""

    roles: List[Dict[str, Any]]


class PermissionListResponse(BaseModel):
    """权限列表响应模型"""

    permissions: List[Dict[str, Any]]


@router.post("/", response_model=ResponseSchema[UserResponse], summary="创建用户")
async def create_user(
    data: UserCreate, db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)
):
    """创建用户"""
    service = UserService(db)
    user = service.create_user(data)
    return success(data=user)


@router.get("/{id}", response_model=ResponseSchema[UserResponse], summary="获取用户详情")
async def get_user(
    id: int = Path(..., description="用户ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户详情"""
    service = UserService()
    user = service.get_user(db, id)
    return success(data=user)


@router.put("/{id}", response_model=ResponseSchema[UserResponse], summary="更新用户")
async def update_user(
    id: int = Path(..., description="用户ID"),
    data: UserUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新用户"""
    service = UserService(db)
    user = service.update_user(id, data)
    return success(data=user)


@router.delete("/{id}", response_model=ResponseSchema[None], summary="删除用户")
async def delete_user(
    id: int = Path(..., description="用户ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除用户"""
    service = UserService(db)
    service.delete_user(id)
    return success(message="用户删除成功")


@router.put("/{id}/role", response_model=ResponseSchema[UserResponse], summary="更新用户角色")
async def update_user_role(
    id: int = Path(..., description="用户ID"),
    data: UserRoleUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新用户角色"""
    service = UserService(db)
    user = service.update_user_role(id, data)
    return success(data=user)


@router.put("/{id}/status", response_model=ResponseSchema[UserResponse], summary="更新用户状态")
async def update_user_status(
    id: int = Path(..., description="用户ID"),
    data: UserStatusUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新用户状态"""
    service = UserService(db)
    user = service.update_user_status(id, data)
    return success(data=user)


@router.put("/{id}/permission", response_model=ResponseSchema[UserResponse], summary="更新用户权限")
async def update_user_permission(
    id: int = Path(..., description="用户ID"),
    data: UserPermissionUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新用户权限"""
    service = UserService(db)
    user = service.update_user_permission(id, data)
    return success(data=user)


@router.get("/me", response_model=ResponseSchema[UserResponse], summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return success(data=current_user)


@router.put("/me", response_model=ResponseSchema[UserResponse], summary="更新当前用户信息")
async def update_current_user_info(
    data: UserUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(async_db)
):
    """更新当前用户信息"""
    service = UserService(db)
    user = service.update_user(current_user.id, data)
    return success(data=user)


@router.get("/roles", response_model=ResponseSchema[RoleListResponse], summary="获取角色列表")
async def get_roles(db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)):
    """获取角色列表"""
    service = UserService(db)
    roles = service.get_roles()
    return success(data=RoleListResponse(roles=roles))


@router.get("/permissions", response_model=ResponseSchema[PermissionListResponse], summary="获取权限列表")
async def get_permissions(db: Session = Depends(async_db), current_user: User = Depends(get_current_active_user)):
    """获取权限列表"""
    service = UserService(db)
    permissions = service.get_permissions()
    return success(data=PermissionListResponse(permissions=permissions))


class ImportResponse(BaseModel):
    """导入响应模型"""

    success: int = 0
    failed: int = 0
    errors: List[str] = []
    details: Dict[str, Any] = {}


@router.post("/import", response_model=ResponseSchema[ImportResponse], summary="导入用户")
async def import_users(
    file: FastAPIUploadFile = File(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导入用户"""
    try:
        service = UserService(db)
        result = service.import_users(file)
        response_data = ImportResponse(**result)
        return success(data=response_data)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"code": 400, "message": str(e), "data": None},
        )


class ExportResponse(BaseModel):
    """导出响应模型"""

    filename: str
    content: bytes
    total: int = 0
    message: str = ""


@router.get(
    "/export",
    response_class=StreamingResponse,
    responses={
        200: {"description": "成功导出用户", "content": {"application/octet-stream": {}}},
        400: {
            "description": "导出失败",
            "content": {"application/json": {"example": {"code": 400, "message": "导出失败", "data": None}}},
        },
    },
)
async def export_users(
    query: str = Query(None, description="搜索关键词"),
    role: str = Query(None, description="角色"),
    status: str = Query(None, description="状态"),
    department_id: int = Query(None, description="部门ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """导出用户"""
    try:
        service = UserService(db)
        result = service.export_users(query=query, role=role, status=status, department_id=department_id)

        # 创建文件流
        content = BytesIO(result["content"])

        # 返回文件流
        return StreamingResponse(
            content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"',
                "X-Total-Count": str(result.get("total", 0)),
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"code": 400, "message": str(e), "data": None}
        )


@router.get("/stats", response_model=ResponseSchema[UserStatsResponse], summary="获取用户统计")
async def get_user_stats(
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取用户统计"""
    service = UserService(db)
    stats = service.get_user_stats(start_time=start_time, end_time=end_time)
    return success(data=UserStatsResponse(**stats))
