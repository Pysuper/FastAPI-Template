from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import (
    BusinessError,
    check_department_capacity,
    check_password_strength,
    contains_sensitive_words,
    validate_regex,
)
from api.v1.endpoints.rbac.rbac import data_permission, require_permissions, require_roles
from api.v1.endpoints.user.logs import log_error, operation_log
from core.exceptions.base.error_codes import ErrorCode
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from core.cache.decorators import cache_decorator, clear_cache
from core.utils.export import DataExporter, DataImporter
from core.utils.query import QueryOptimizer
from models.user import User
from models.role import Role
from models.department import Department
from schemas.user import UserResponse, UserCreate, UserUpdate, UserPasswordUpdate
from utils.security import get_password_hash, verify_password

router = APIRouter()


@router.post("/", response_model=ResponseSchema[UserResponse])
@operation_log(module="用户管理", action="创建用户")
@require_permissions("user:create")
@require_roles("admin")
async def create_user(
    user: UserCreate, request: Request, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """创建用户"""
    # 验证用户名
    if not validate_regex(user.username, "username"):
        raise BusinessError(ErrorCode.INVALID_USERNAME, "用户名格式不正确")

    # 检查敏感词
    if contains_sensitive_words(user.username):
        raise BusinessError(ErrorCode.SENSITIVE_USERNAME, "用户名包含敏感词")

    # 检查密码强度
    if not check_password_strength(user.password):
        raise BusinessError(ErrorCode.WEAK_PASSWORD, "密码强度不足")

    # 检查部门容量
    if not check_department_capacity(user.department_id, db):
        raise BusinessError(ErrorCode.DEPARTMENT_FULL, "部门人数已满")

    try:
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == user.username, User.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Username already exists")

        # 检查邮箱是否已存在
        if user.email and db.query(User).filter(User.email == user.email, User.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Email already exists")

        # 检查手机号是否已存在
        if user.phone and db.query(User).filter(User.phone == user.phone, User.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Phone number already exists")

        # 检查部门是否存在
        if user.department_id and not db.query(Department).filter(Department.id == user.department_id).first():
            raise HTTPException(status_code=404, detail="Department not found")

        # 检查角色是否存在
        if user.role_ids:
            for role_id in user.role_ids:
                if not db.query(Role).filter(Role.id == role_id).first():
                    raise HTTPException(status_code=404, detail=f"Role {role_id} not found")

        # 创建用户
        db_user = User(
            username=user.username,
            password_hash=get_password_hash(user.password),
            email=user.email,
            phone=user.phone,
            real_name=user.real_name,
            avatar=user.avatar,
            department_id=user.department_id,
            role_ids=user.role_ids,
            is_superuser=user.is_superuser,
            remark=user.remark,
            create_by=current_user,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # 清除相关缓存
        clear_cache("user:*")
        clear_cache("role:user:*")
        clear_cache("department:user:*")

        return success(data=db_user)

    except Exception as e:
        await log_error(db=db, module="用户管理", action="创建用户", error=e, user_id=current_user, request=request)
        raise


@router.get("/{user_id}", response_model=ResponseSchema[UserResponse])
@cache_decorator(prefix="user", expire=3600)
async def get_user(user_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id, User.is_delete == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return success(data=user)


@router.put("/{user_id}", response_model=ResponseSchema[UserResponse])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id, User.is_delete == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 检查邮箱是否已存在
    if (
        user_update.email
        and db.query(User).filter(User.email == user_update.email, User.id != user_id, User.is_delete == False).first()
    ):
        raise HTTPException(status_code=400, detail="Email already exists")

    # 检查手机号是否已存在
    if (
        user_update.phone
        and db.query(User).filter(User.phone == user_update.phone, User.id != user_id, User.is_delete == False).first()
    ):
        raise HTTPException(status_code=400, detail="Phone number already exists")

    # 检查部门是否存在
    if (
        user_update.department_id
        and not db.query(Department).filter(Department.id == user_update.department_id).first()
    ):
        raise HTTPException(status_code=404, detail="Department not found")

    # 检查角色是否存在
    if user_update.role_ids:
        for role_id in user_update.role_ids:
            if not db.query(Role).filter(Role.id == role_id).first():
                raise HTTPException(status_code=404, detail=f"Role {role_id} not found")

    # 检查状态是否有效
    if user_update.status:
        valid_statuses = ["active", "disabled", "locked"]
        if user_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)

    user.update_by = current_user
    user.update_time = datetime.now()

    db.add(user)
    db.commit()
    db.refresh(user)

    # 清除相关缓存
    clear_cache(f"user:{user_id}")
    clear_cache("user:list:*")
    if user_update.department_id:
        clear_cache("department:user:*")
    if user_update.role_ids:
        clear_cache("role:user:*")

    return success(data=user)


@router.delete("/{user_id}", response_model=ResponseSchema)
async def delete_user(user_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id, User.is_delete == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 不能删除超级管理员
    if user.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot delete superuser")

    user.is_delete = True
    user.delete_by = current_user
    user.delete_time = datetime.now()

    db.add(user)
    db.commit()

    # 清除相关缓存
    clear_cache(f"user:{user_id}")
    clear_cache("user:list:*")
    clear_cache("role:user:*")
    clear_cache("department:user:*")

    return success(message="User deleted successfully")


@router.get("/", response_model=ResponseSchema[List[UserResponse]])
@operation_log(module="用户管理", action="获取用户列表")
@require_permissions("user:list")
@data_permission("User", "department_id")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    department_id: Optional[int] = None,
    role_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取用户列表"""
    # 构建查询条件
    filters = {}
    if keyword:
        filters["or"] = [
            {"username": {"ilike": f"%{keyword}%"}},
            {"real_name": {"ilike": f"%{keyword}%"}},
            {"email": {"ilike": f"%{keyword}%"}},
            {"phone": {"ilike": f"%{keyword}%"}},
        ]
    if department_id:
        filters["department_id"] = department_id
    if role_id:
        filters["role_ids"] = {"contains": [role_id]}
    if status:
        filters["status"] = status

    # 构建排序条件
    order_by = ["create_time desc"]

    # 执行查询
    result = QueryOptimizer.build_query(
        db=db,
        model=User,
        filters=filters,
        order_by=order_by,
        page=skip // limit + 1,
        page_size=limit,
        cache_key=f"user:list:{skip}:{limit}:{keyword}:{department_id}:{role_id}:{status}",
        cache_expire=300,
    )

    return success(data=result[0], meta={"total": result[1], "skip": skip, "limit": limit})


@router.put("/{user_id}/password", response_model=ResponseSchema)
async def update_password(
    user_id: int,
    password_update: UserPasswordUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新用户密码"""
    user = db.query(User).filter(User.id == user_id, User.is_delete == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 验证旧密码
    if not verify_password(password_update.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    user.password_hash = get_password_hash(password_update.new_password)
    user.update_by = current_user
    user.update_time = datetime.now()

    db.add(user)
    db.commit()
    return success(message="Password updated successfully")


@router.put("/{user_id}/status", response_model=ResponseSchema[UserResponse])
async def update_user_status(
    user_id: int, status: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """更新用户状态"""
    user = db.query(User).filter(User.id == user_id, User.is_delete == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 不能修改超级管理员状态
    if user.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot modify superuser status")

    valid_statuses = ["active", "disabled", "locked"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    user.status = status
    user.update_by = current_user
    user.update_time = datetime.now()

    db.add(user)
    db.commit()
    db.refresh(user)
    return success(data=user)


@router.put("/{user_id}/roles", response_model=ResponseSchema[UserResponse])
async def update_user_roles(
    user_id: int, role_ids: List[int], db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """更新用户角色"""
    user = db.query(User).filter(User.id == user_id, User.is_delete == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 检查角色是否存在
    for role_id in role_ids:
        if not db.query(Role).filter(Role.id == role_id).first():
            raise HTTPException(status_code=404, detail=f"Role {role_id} not found")

    user.role_ids = role_ids
    user.update_by = current_user
    user.update_time = datetime.now()

    db.add(user)
    db.commit()
    db.refresh(user)
    return success(data=user)


@router.get("/stats", response_model=ResponseSchema)
@cache_decorator(prefix="user:stats", expire=300)
async def get_user_stats(
    department_id: Optional[int] = None, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """获取用户统计信息"""
    query = db.query(User).filter(User.is_delete == False)

    if department_id:
        query = query.filter(User.department_id == department_id)

    total_users = query.count()
    active_users = query.filter(User.status == "active").count()
    disabled_users = query.filter(User.status == "disabled").count()
    locked_users = query.filter(User.status == "locked").count()

    # 部门分布
    department_distribution = {
        dept.name: count
        for dept, count in db.query(Department, func.count(User.id))
        .join(User, User.department_id == Department.id)
        .filter(User.is_delete == False)
        .group_by(Department)
        .all()
    }

    # 角色分布
    role_distribution = {}
    roles = db.query(Role).all()
    for role in roles:
        count = query.filter(User.role_ids.contains([role.id])).count()
        role_distribution[role.name] = count

    # 登录统计
    login_stats = (
        db.query(
            func.avg(User.login_count).label("avg_login_count"),
            func.max(User.login_count).label("max_login_count"),
            func.min(User.login_count).label("min_login_count"),
        )
        .filter(User.is_delete == False)
        .first()
    )

    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "disabled_users": disabled_users,
        "locked_users": locked_users,
        "department_distribution": department_distribution,
        "role_distribution": role_distribution,
        "login_stats": {
            "average": login_stats.avg_login_count or 0,
            "maximum": login_stats.max_login_count or 0,
            "minimum": login_stats.min_login_count or 0,
        },
    }

    return success(data=stats)


@router.post("/import", response_model=ResponseSchema)
@require_permissions("user:import")
async def import_users(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导入用户数据"""
    # 检查文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 保存文件
    filename = f"temp/user_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
    with open(filename, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # 导入数据
        if file_ext == "csv":
            imported_count = DataImporter.import_from_csv(filename, User, db)
        elif file_ext == "xlsx":
            imported_count = DataImporter.import_from_excel(filename, User, db)
        else:
            imported_count = DataImporter.import_from_json(filename, User, db)

        # 清除缓存
        clear_cache("user:*")
        clear_cache("role:user:*")
        clear_cache("department:user:*")

        return success(message=f"Successfully imported {imported_count} users")

    finally:
        # 删除临时文件
        import os

        os.remove(filename)


@router.get("/export", response_model=ResponseSchema)
@require_permissions("user:export")
async def export_users(file_type: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """导出用户数据"""
    # 检查文件类型
    if file_type not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 查询数据
    users = db.query(User).filter(User.is_delete == False).all()
    data = [
        {
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "real_name": user.real_name,
            "department_id": user.department_id,
            "role_ids": user.role_ids,
            "status": user.status,
            "remark": user.remark,
        }
        for user in users
    ]

    # 导出文件
    filename = f"temp/user_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_type}"
    fields = ["username", "email", "phone", "real_name", "department_id", "role_ids", "status", "remark"]

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

        return success(data={"filename": f"users.{file_type}", "content": content})

    finally:
        # 删除临时文件
        import os

        os.remove(filename)
