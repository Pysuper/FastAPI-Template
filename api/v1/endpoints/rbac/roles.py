from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import (
    BusinessError,
    ErrorCode,
    check_permission_conflicts,
    check_role_depth,
    validate_regex,
)
from api.v1.endpoints.rbac.decorators import require_permissions, require_roles
from api.v1.endpoints.user.logs import log_error
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.models import Role, User
from interceptor.response import ResponseSchema, success
from core.schemas.roles import RoleCreate, RoleResponse, RoleUpdate
from core.utils.logging import operation_log

# 路由
router = APIRouter()


@router.post("/", response_model=ResponseSchema[RoleResponse])
@operation_log(module="角色管理", action="创建角色")
@require_permissions("role:create")
@require_roles("admin")
async def create_role(
    role: RoleCreate, request: Request, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """创建角色"""
    # 验证角色编码
    if not validate_regex(role.code, "role_code"):
        raise BusinessError(ErrorCode.INVALID_ROLE_CODE, "角色编码格式不正确")

    # 检查角色层级深度
    if not check_role_depth(role.parent_id, db):
        raise BusinessError(ErrorCode.ROLE_DEPTH_EXCEEDED, "角色层级超出限制")

    # 检查权限冲突
    if check_permission_conflicts(role.permission_ids, db):
        raise BusinessError(ErrorCode.PERMISSION_CONFLICT, "存在冲突的权限")

    try:
        # 检查角色名称是否已存在
        if db.query(Role).filter(Role.name == role.name, Role.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Role name already exists")

        # 检查角色编码是否已存在
        if db.query(Role).filter(Role.code == role.code, Role.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Role code already exists")

        # 检查父级角色是否存在
        if role.parent_id and not db.query(Role).filter(Role.id == role.parent_id).first():
            raise HTTPException(status_code=404, detail="Parent role not found")

        # 创建角色
        db_role = Role(
            name=role.name,
            code=role.code,
            description=role.description,
            permission_ids=role.permission_ids,
            menu_ids=role.menu_ids,
            parent_id=role.parent_id,
            sort=role.sort,
            is_system=role.is_system,
            remark=role.remark,
            create_by=current_user,
        )
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return success(data=db_role)

    except Exception as e:
        # 记录错误日志
        await log_error(db=db, module="角色管理", action="创建角色", error=e, user_id=current_user, request=request)
        raise


@router.get("/{role_id}", response_model=ResponseSchema[RoleResponse])
async def get_role(role_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取角色详情"""
    role = db.query(Role).filter(Role.id == role_id, Role.is_delete == False).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return success(data=role)


@router.put("/{role_id}", response_model=ResponseSchema[RoleResponse])
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新角色信息"""
    role = db.query(Role).filter(Role.id == role_id, Role.is_delete == False).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # 不能修改系统角色
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system role")

    # 检查角色名称是否已存在
    if (
        role_update.name
        and db.query(Role).filter(Role.name == role_update.name, Role.id != role_id, Role.is_delete == False).first()
    ):
        raise HTTPException(status_code=400, detail="Role name already exists")

    # 检查角色编码是否已存在
    if (
        role_update.code
        and db.query(Role).filter(Role.code == role_update.code, Role.id != role_id, Role.is_delete == False).first()
    ):
        raise HTTPException(status_code=400, detail="Role code already exists")

    # 检查父级角色是否存在
    if role_update.parent_id and not db.query(Role).filter(Role.id == role_update.parent_id).first():
        raise HTTPException(status_code=404, detail="Parent role not found")

    # 检查状态是否有效
    if role_update.status:
        valid_statuses = ["active", "disabled"]
        if role_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    for field, value in role_update.dict(exclude_unset=True).items():
        setattr(role, field, value)

    role.update_by = current_user
    role.update_time = datetime.now()

    db.add(role)
    db.commit()
    db.refresh(role)
    return success(data=role)


@router.delete("/{role_id}", response_model=ResponseSchema)
async def delete_role(role_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """删除角色"""
    role = db.query(Role).filter(Role.id == role_id, Role.is_delete == False).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # 不能删除系统角色
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")

    # 检查是否有用户使用该角色
    if db.query(User).filter(User.role_ids.contains([role_id]), User.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Role is in use by users")

    # 检查是否有子角色
    if db.query(Role).filter(Role.parent_id == role_id, Role.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Role has child roles")

    role.is_delete = True
    role.delete_by = current_user
    role.delete_time = datetime.now()

    db.add(role)
    db.commit()
    return success(message="Role deleted successfully")


@router.get("/", response_model=ResponseSchema[List[RoleResponse]])
@operation_log(module="角色管理", action="获取角色列表")
@require_permissions("role:list")
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取角色列表"""
    query = db.query(Role).filter(Role.is_delete == False)

    if keyword:
        query = query.filter(
            or_(
                Role.name.ilike(f"%{keyword}%"),
                Role.code.ilike(f"%{keyword}%"),
                Role.description.ilike(f"%{keyword}%"),
            )
        )
    if status:
        query = query.filter(Role.status == status)

    total = query.count()
    roles = query.order_by(Role.sort.asc()).offset(skip).limit(limit).all()

    return success(data=roles, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{role_id}/status", response_model=ResponseSchema[RoleResponse])
async def update_role_status(
    role_id: int, status: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """更新角色状态"""
    role = db.query(Role).filter(Role.id == role_id, Role.is_delete == False).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # 不能修改系统角色状态
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system role status")

    valid_statuses = ["active", "disabled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    role.status = status
    role.update_by = current_user
    role.update_time = datetime.now()

    db.add(role)
    db.commit()
    db.refresh(role)
    return success(data=role)


@router.get("/stats", response_model=ResponseSchema)
async def get_role_stats(db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取角色统计信息"""
    query = db.query(Role).filter(Role.is_delete == False)

    total_roles = query.count()
    active_roles = query.filter(Role.status == "active").count()
    disabled_roles = query.filter(Role.status == "disabled").count()
    system_roles = query.filter(Role.is_system == True).count()

    # 权限分布
    permission_distribution = {}
    roles = query.all()
    for role in roles:
        permission_count = len(role.permission_ids)
        if permission_count in permission_distribution:
            permission_distribution[permission_count] += 1
        else:
            permission_distribution[permission_count] = 1

    # 菜单分布
    menu_distribution = {}
    for role in roles:
        menu_count = len(role.menu_ids)
        if menu_count in menu_distribution:
            menu_distribution[menu_count] += 1
        else:
            menu_distribution[menu_count] = 1

    # 用户分布
    user_distribution = {}
    for role in roles:
        user_count = db.query(User).filter(User.role_ids.contains([role.id]), User.is_delete == False).count()
        user_distribution[role.name] = user_count

    stats = {
        "total_roles": total_roles,
        "active_roles": active_roles,
        "disabled_roles": disabled_roles,
        "system_roles": system_roles,
        "permission_distribution": permission_distribution,
        "menu_distribution": menu_distribution,
        "user_distribution": user_distribution,
    }

    return success(data=stats)
