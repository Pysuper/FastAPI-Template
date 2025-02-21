from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import BusinessError, ErrorCode, check_permission_dependencies, validate_regex
from api.v1.endpoints.rbac.decorators import require_permissions, require_roles
from api.v1.endpoints.user.logs import log_error
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.models import Permission, Role
from interceptor.response import ResponseSchema, success
from core.schemas.permission import PermissionCreate, PermissionResponse, PermissionUpdate
from core.utils.logging import operation_log

router = APIRouter()


@router.post("/", response_model=ResponseSchema[PermissionResponse])
@operation_log(module="权限管理", action="创建权限")
@require_permissions("permission:create")
@require_roles("admin")
async def create_permission(
    permission: PermissionCreate,
    request: Request,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建权限"""
    # 验证权限编码
    if not validate_regex(permission.code, "permission_code"):
        raise BusinessError(ErrorCode.INVALID_PERMISSION_CODE, "权限编码格式不正确")

    # 检查权限依赖关系
    if not check_permission_dependencies(permission.parent_id, db):
        raise BusinessError(ErrorCode.PERMISSION_DEPENDENCY_ERROR, "父级权限不可用")

    try:
        # 检查权限名称是否已存在
        if db.query(Permission).filter(Permission.name == permission.name, Permission.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Permission name already exists")

        # 检查权限编码是否已存在
        if db.query(Permission).filter(Permission.code == permission.code, Permission.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Permission code already exists")

        # 检查父级权限是否存在
        if permission.parent_id and not db.query(Permission).filter(Permission.id == permission.parent_id).first():
            raise HTTPException(status_code=404, detail="Parent permission not found")

        # 检查权限类型是否有效
        valid_types = ["menu", "button", "api"]
        if permission.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {', '.join(valid_types)}")

        # 创建权限
        db_permission = Permission(
            name=permission.name,
            code=permission.code,
            description=permission.description,
            type=permission.type,
            parent_id=permission.parent_id,
            module=permission.module,
            sort=permission.sort,
            is_system=permission.is_system,
            remark=permission.remark,
            create_by=current_user,
        )
        db.add(db_permission)
        db.commit()
        db.refresh(db_permission)
        return success(data=db_permission)

    except Exception as e:
        # 记录错误日志
        await log_error(db=db, module="权限管理", action="创建权限", error=e, user_id=current_user, request=request)
        raise


@router.get("/{permission_id}", response_model=ResponseSchema[PermissionResponse])
async def get_permission(
    permission_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """获取权限详情"""
    permission = db.query(Permission).filter(Permission.id == permission_id, Permission.is_delete == False).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return success(data=permission)


@router.put("/{permission_id}", response_model=ResponseSchema[PermissionResponse])
async def update_permission(
    permission_id: int,
    permission_update: PermissionUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新权限信息"""
    permission = db.query(Permission).filter(Permission.id == permission_id, Permission.is_delete == False).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    # 不能修改系统权限
    if permission.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system permission")

    # 检查权限名称是否已存在
    if (
        permission_update.name
        and db.query(Permission)
        .filter(
            Permission.name == permission_update.name, Permission.id != permission_id, Permission.is_delete == False
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Permission name already exists")

    # 检查权限编码是否已存在
    if (
        permission_update.code
        and db.query(Permission)
        .filter(
            Permission.code == permission_update.code, Permission.id != permission_id, Permission.is_delete == False
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Permission code already exists")

    # 检查父级权限是否存在
    if (
        permission_update.parent_id
        and not db.query(Permission).filter(Permission.id == permission_update.parent_id).first()
    ):
        raise HTTPException(status_code=404, detail="Parent permission not found")

    # 检查权限类型是否有效
    if permission_update.type:
        valid_types = ["menu", "button", "api"]
        if permission_update.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {', '.join(valid_types)}")

    # 检查状态是否有效
    if permission_update.status:
        valid_statuses = ["active", "disabled"]
        if permission_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    for field, value in permission_update.dict(exclude_unset=True).items():
        setattr(permission, field, value)

    permission.update_by = current_user
    permission.update_time = datetime.now()

    db.add(permission)
    db.commit()
    db.refresh(permission)
    return success(data=permission)


@router.delete("/{permission_id}", response_model=ResponseSchema)
async def delete_permission(
    permission_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """删除权限"""
    permission = db.query(Permission).filter(Permission.id == permission_id, Permission.is_delete == False).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    # 不能删除系统权限
    if permission.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system permission")

    # 检查是否有角色使用该权限
    if db.query(Role).filter(Role.permission_ids.contains([permission_id]), Role.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Permission is in use by roles")

    # 检查是否有子权限
    if db.query(Permission).filter(Permission.parent_id == permission_id, Permission.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Permission has child permissions")

    permission.is_delete = True
    permission.delete_by = current_user
    permission.delete_time = datetime.now()

    db.add(permission)
    db.commit()
    return success(message="Permission deleted successfully")


@router.get("/", response_model=ResponseSchema[List[PermissionResponse]])
@operation_log(module="权限管理", action="获取权限列表")
@require_permissions("permission:list")
async def list_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    module: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取权限列表"""
    query = db.query(Permission).filter(Permission.is_delete == False)

    if keyword:
        query = query.filter(
            or_(
                Permission.name.ilike(f"%{keyword}%"),
                Permission.code.ilike(f"%{keyword}%"),
                Permission.description.ilike(f"%{keyword}%"),
            )
        )
    if type:
        query = query.filter(Permission.type == type)
    if module:
        query = query.filter(Permission.module == module)
    if status:
        query = query.filter(Permission.status == status)

    total = query.count()
    permissions = query.order_by(Permission.sort.asc()).offset(skip).limit(limit).all()

    return success(data=permissions, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{permission_id}/status", response_model=ResponseSchema[PermissionResponse])
async def update_permission_status(
    permission_id: int, status: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """更新权限状态"""
    permission = db.query(Permission).filter(Permission.id == permission_id, Permission.is_delete == False).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    # 不能修改系统权限状态
    if permission.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system permission status")

    valid_statuses = ["active", "disabled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    permission.status = status
    permission.update_by = current_user
    permission.update_time = datetime.now()

    db.add(permission)
    db.commit()
    db.refresh(permission)
    return success(data=permission)


@router.get("/stats", response_model=ResponseSchema)
async def get_permission_stats(db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取权限统计信息"""
    query = db.query(Permission).filter(Permission.is_delete == False)

    total_permissions = query.count()
    active_permissions = query.filter(Permission.status == "active").count()
    disabled_permissions = query.filter(Permission.status == "disabled").count()
    system_permissions = query.filter(Permission.is_system == True).count()

    # 类型分布
    type_distribution = {}
    for type in ["menu", "button", "api"]:
        count = query.filter(Permission.type == type).count()
        type_distribution[type] = count

    # 模块分布
    module_distribution = {
        module: count
        for module, count in db.query(Permission.module, func.count(Permission.id))
        .filter(Permission.is_delete == False)
        .group_by(Permission.module)
        .all()
    }

    # 角色分布
    role_distribution = {}
    permissions = query.all()
    for permission in permissions:
        role_count = (
            db.query(Role).filter(Role.permission_ids.contains([permission.id]), Role.is_delete == False).count()
        )
        role_distribution[permission.name] = role_count

    stats = {
        "total_permissions": total_permissions,
        "active_permissions": active_permissions,
        "disabled_permissions": disabled_permissions,
        "system_permissions": system_permissions,
        "type_distribution": type_distribution,
        "module_distribution": module_distribution,
        "role_distribution": role_distribution,
    }

    return success(data=stats)
