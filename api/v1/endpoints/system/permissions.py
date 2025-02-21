from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import validate_regex, BusinessError, check_permission_dependencies
from api.v1.endpoints.rbac.decorators import require_permissions, require_roles
from api.v1.endpoints.user.logs import log_error
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.exceptions.base.error_codes import ErrorCode
from models import Permission
from models import Role
from interceptor.response import ResponseSchema, success
from schemas.permission import PermissionResponse, PermissionCreate, PermissionUpdate
from core.cache.decorators import clear_cache, cache_decorator
from core.utils.export import DataImporter, DataExporter
from core.utils.logging import operation_log
from core.utils.query import QueryOptimizer

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

        # 清除相关缓存
        clear_cache("permission:*")
        clear_cache("role:permission:*")

        return success(data=db_permission)

    except Exception as e:
        # 记录错误日志
        await log_error(db=db, module="权限管理", action="创建权限", error=e, user_id=current_user, request=request)
        raise


@router.get("/{permission_id}", response_model=ResponseSchema[PermissionResponse])
@cache_decorator(prefix="permission", expire=3600)
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

    # 清除相关缓存
    clear_cache(f"permission:{permission_id}")
    clear_cache("permission:list:*")
    clear_cache("role:permission:*")

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

    # 清除相关缓存
    clear_cache(f"permission:{permission_id}")
    clear_cache("permission:list:*")
    clear_cache("role:permission:*")

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
    # 构建查询条件
    filters = {}
    if keyword:
        filters["or"] = [
            {"name": {"ilike": f"%{keyword}%"}},
            {"code": {"ilike": f"%{keyword}%"}},
            {"description": {"ilike": f"%{keyword}%"}},
        ]
    if type:
        filters["type"] = type
    if module:
        filters["module"] = module
    if status:
        filters["status"] = status

    # 构建排序条件
    order_by = ["sort asc", "create_time desc"]

    # 执行查询
    result = QueryOptimizer.build_query(
        db=db,
        model=Permission,
        filters=filters,
        order_by=order_by,
        page=skip // limit + 1,
        page_size=limit,
        cache_key=f"permission:list:{skip}:{limit}:{keyword}:{type}:{module}:{status}",
        cache_expire=300,
    )

    return success(data=result[0], meta={"total": result[1], "skip": skip, "limit": limit})


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
@cache_decorator(prefix="permission:stats", expire=300)
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


@router.post("/import", response_model=ResponseSchema)
@require_permissions("permission:import")
async def import_permissions(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导入权限数据"""
    # 检查文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 保存文件
    filename = f"temp/permission_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
    with open(filename, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # 导入数据
        if file_ext == "csv":
            imported_count = DataImporter.import_from_csv(filename, Permission, db)
        elif file_ext == "xlsx":
            imported_count = DataImporter.import_from_excel(filename, Permission, db)
        else:
            imported_count = DataImporter.import_from_json(filename, Permission, db)

        # 清除缓存
        clear_cache("permission:*")
        clear_cache("role:permission:*")

        return success(message=f"Successfully imported {imported_count} permissions")

    finally:
        # 删除临时文件
        import os

        os.remove(filename)


@router.get("/export", response_model=ResponseSchema)
@require_permissions("permission:export")
async def export_permissions(
    file_type: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导出权限数据"""
    # 检查文件类型
    if file_type not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 查询数据
    permissions = db.query(Permission).filter(Permission.is_delete == False).all()
    data = [
        {
            "name": permission.name,
            "code": permission.code,
            "description": permission.description,
            "type": permission.type,
            "parent_id": permission.parent_id,
            "module": permission.module,
            "sort": permission.sort,
            "status": permission.status,
            "is_system": permission.is_system,
            "remark": permission.remark,
        }
        for permission in permissions
    ]

    # 导出文件
    filename = f"temp/permission_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_type}"
    fields = ["name", "code", "description", "type", "parent_id", "module", "sort", "status", "is_system", "remark"]

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

        return success(data={"filename": f"permissions.{file_type}", "content": content})

    finally:
        # 删除临时文件
        import os

        os.remove(filename)
