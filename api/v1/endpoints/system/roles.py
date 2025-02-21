from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import validate_regex, BusinessError, check_role_depth, check_permission_conflicts
from api.v1.endpoints.rbac.decorators import require_permissions, require_roles
from api.v1.endpoints.user.logs import log_error
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.exceptions.base.error_codes import ErrorCode
from interceptor.response import ResponseSchema, success
from core.cache.decorators import clear_cache, cache_decorator
from core.utils.export import DataImporter, DataExporter
from core.utils.logging import operation_log
from core.utils.query import QueryOptimizer
from models import Role
from models.user import User
from schemas import RoleResponse, RoleCreate, RoleUpdate

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

        # 清除相关缓存
        clear_cache("role:*")
        clear_cache("permission:role:*")
        clear_cache("menu:role:*")

        return success(data=db_role)

    except Exception as e:
        # 记录错误日志
        await log_error(db=db, module="角色管理", action="创建角色", error=e, user_id=current_user, request=request)
        raise


@router.get("/{role_id}", response_model=ResponseSchema[RoleResponse])
@cache_decorator(prefix="role", expire=3600)
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

    # 清除相关缓存
    clear_cache(f"role:{role_id}")
    clear_cache("role:list:*")
    if role_update.permission_ids:
        clear_cache("permission:role:*")
    if role_update.menu_ids:
        clear_cache("menu:role:*")

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

    # 清除相关缓存
    clear_cache(f"role:{role_id}")
    clear_cache("role:list:*")
    clear_cache("permission:role:*")
    clear_cache("menu:role:*")

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
    # 构建查询条件
    filters = {}
    if keyword:
        filters["or"] = [
            {"name": {"ilike": f"%{keyword}%"}},
            {"code": {"ilike": f"%{keyword}%"}},
            {"description": {"ilike": f"%{keyword}%"}},
        ]
    if status:
        filters["status"] = status

    # 构建排序条件
    order_by = ["sort asc", "create_time desc"]

    # 执行查询
    result = QueryOptimizer.build_query(
        db=db,
        model=Role,
        filters=filters,
        order_by=order_by,
        page=skip // limit + 1,
        page_size=limit,
        cache_key=f"role:list:{skip}:{limit}:{keyword}:{status}",
        cache_expire=300,
    )

    return success(data=result[0], meta={"total": result[1], "skip": skip, "limit": limit})


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
@cache_decorator(prefix="role:stats", expire=300)
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


@router.post("/import", response_model=ResponseSchema)
@require_permissions("role:import")
async def import_roles(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导入角色数据"""
    # 检查文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 保存文件
    filename = f"temp/role_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
    with open(filename, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # 导入数据
        if file_ext == "csv":
            imported_count = DataImporter.import_from_csv(filename, Role, db)
        elif file_ext == "xlsx":
            imported_count = DataImporter.import_from_excel(filename, Role, db)
        else:
            imported_count = DataImporter.import_from_json(filename, Role, db)

        # 清除缓存
        clear_cache("role:*")
        clear_cache("permission:role:*")
        clear_cache("menu:role:*")

        return success(message=f"Successfully imported {imported_count} roles")

    finally:
        # 删除临时文件
        import os

        os.remove(filename)


@router.get("/export", response_model=ResponseSchema)
@require_permissions("role:export")
async def export_roles(file_type: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """导出角色数据"""
    # 检查文件类型
    if file_type not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 查询数据
    roles = db.query(Role).filter(Role.is_delete == False).all()
    data = [
        {
            "name": role.name,
            "code": role.code,
            "description": role.description,
            "permission_ids": role.permission_ids,
            "menu_ids": role.menu_ids,
            "parent_id": role.parent_id,
            "sort": role.sort,
            "status": role.status,
            "is_system": role.is_system,
            "remark": role.remark,
        }
        for role in roles
    ]

    # 导出文件
    filename = f"temp/role_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_type}"
    fields = [
        "name",
        "code",
        "description",
        "permission_ids",
        "menu_ids",
        "parent_id",
        "sort",
        "status",
        "is_system",
        "remark",
    ]

    try:
        if file_type == "csv":
            DataExporter.export_to_csv(data, fields, filename)
        elif file_type == "xlsx":
            DataExporter.export_to_excel(data, fields, filename)
        else:
            DataExporter.export_to_json(data, filename)

        # 读取文件内容
        with open(filename, "rb") as f:
            content = f.read()

        return success(data={"filename": f"roles.{file_type}", "content": content})

    finally:
        # 删除临时文件
        import os

        os.remove(filename)
