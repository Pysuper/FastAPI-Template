from datetime import datetime
from typing import List, Optional

from aiohttp.abc import Request
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session

from api.v1.endpoints.files.tools import (
    BusinessError,
    check_department_capacity,
    check_password_strength,
    contains_sensitive_words,
    validate_regex,
)
from core.dependencies import async_db
from core.exceptions.base.error_codes import ErrorCode
from core.models import Role, User
from interceptor.response import ResponseSchema, success
from core.schemas.user import UserPasswordUpdate
from security.core.security import get_current_user
from security.auth.utils import get_password_hash, verify_password
from core.utils.logging import operation_log
from models.department import Department
from schemas.user import UserCreate, UserResponse, UserUpdate
from .decorators import data_permission, require_permissions, require_roles
from ..user.logs import log_error

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
        return success(data=db_user)

    except Exception as e:
        # 记录错误日志
        await log_error(db=db, module="用户管理", action="创建用户", error=e, user_id=current_user, request=request)
        raise


@router.get("/{user_id}", response_model=ResponseSchema[UserResponse])
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
    query = db.query(User).filter(User.is_delete == False)

    if keyword:
        query = query.filter(
            or_(
                User.username.ilike(f"%{keyword}%"),
                User.real_name.ilike(f"%{keyword}%"),
                User.email.ilike(f"%{keyword}%"),
                User.phone.ilike(f"%{keyword}%"),
            )
        )
    if department_id:
        query = query.filter(User.department_id == department_id)
    if role_id:
        query = query.filter(User.role_ids.contains([role_id]))
    if status:
        query = query.filter(User.status == status)

    total = query.count()
    users = query.offset(skip).limit(limit).all()

    return success(data=users, meta={"total": total, "skip": skip, "limit": limit})


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
