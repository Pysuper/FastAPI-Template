from functools import wraps
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import BusinessError
from core.dependencies import async_db
from exceptions.base.error_codes import ErrorCode
from security.core.security import get_current_user
from models.department import Department
from models.menu import Menu
from models.permission import Permission
from models.role import Role
from models.user import User
from schemas.validators.rbac import PermissionCreate, PermissionSchema, RoleCreate, RoleSchema
from .decorators import require_permissions, require_roles, data_permission

router = APIRouter(prefix="/rbac", tags=["RBAC"])

# 导出装饰器供其他模块使用
__all__ = ["require_permissions", "require_roles", "data_permission"]


# 角色管理
@router.post("/roles", response_model=RoleSchema)
async def create_role(
    *,
    db: AsyncSession = Depends(async_db),
    role_in: RoleCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """创建角色"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can create roles",
        )

    role = Role(name=role_in.name, description=role_in.description)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.get("/roles", response_model=List[RoleSchema])
async def get_roles(
    db: AsyncSession = Depends(async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取所有角色"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can view all roles",
        )

    result = await db.execute(select(Role))
    roles = result.scalars().all()
    return roles


# 权限管理
@router.post("/permissions", response_model=PermissionSchema)
async def create_permission(
    *,
    db: AsyncSession = Depends(async_db),
    permission_in: PermissionCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """创建权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can create permissions",
        )

    permission = Permission(
        name=permission_in.name,
        description=permission_in.description,
        resource=permission_in.resource,
        action=permission_in.action,
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission


@router.get("/permissions", response_model=List[PermissionSchema])
async def get_permissions(
    db: AsyncSession = Depends(async_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取所有权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can view all permissions",
        )

    result = await db.execute(select(Permission))
    permissions = result.scalars().all()
    return permissions


# 角色-权限管理
@router.post("/roles/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(
    *,
    db: AsyncSession = Depends(async_db),
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """为角色分配权限"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can assign permissions",
        )

    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    permission = await db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    role.permissions.append(permission)
    await db.commit()
    return {"status": "success"}


# 用户-角色管理
@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    *,
    db: AsyncSession = Depends(async_db),
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """为用户分配角色"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can assign roles",
        )

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    user.roles.append(role)
    await db.commit()
    return {"status": "success"}


def get_user_permissions(user_id: int, db: Session) -> List[str]:
    """获取用户所有权限编码"""
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []

    # 如果是超级管理员
    if user.is_superuser:
        return [p.code for p in db.query(Permission).all()]

    # 获取用户角色
    roles = db.query(Role).filter(Role.id.in_(user.role_ids), Role.status == "active", Role.is_delete == False).all()

    # 获取角色权限
    permission_ids = set()
    for role in roles:
        permission_ids.update(role.permission_ids)

    # 获取权限编码
    permissions = (
        db.query(Permission)
        .filter(Permission.id.in_(permission_ids), Permission.status == "active", Permission.is_delete == False)
        .all()
    )

    return [p.code for p in permissions]


def get_user_menus(user_id: int, db: Session) -> List[dict]:
    """获取用户菜单"""
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []

    # 如果是超级管理员
    if user.is_superuser:
        menus = (
            db.query(Menu)
            .filter(Menu.type == "menu", Menu.status == "active", Menu.is_visible == True, Menu.is_delete == False)
            .all()
        )
        return build_menu_tree(menus)

    # 获取用户角色
    roles = db.query(Role).filter(Role.id.in_(user.role_ids), Role.status == "active", Role.is_delete == False).all()

    # 获取角色菜单
    menu_ids = set()
    for role in roles:
        menu_ids.update(role.menu_ids)

    # 获取菜单
    menus = (
        db.query(Menu)
        .filter(
            Menu.id.in_(menu_ids),
            Menu.type == "menu",
            Menu.status == "active",
            Menu.is_visible == True,
            Menu.is_delete == False,
        )
        .all()
    )

    return build_menu_tree(menus)


def build_menu_tree(menus: List[Menu], parent_id: Optional[int] = None) -> List[dict]:
    """构建菜单树"""
    tree = []
    for menu in menus:
        if menu.parent_id == parent_id:
            node = {
                "id": menu.id,
                "name": menu.name,
                "path": menu.path,
                "component": menu.component,
                "icon": menu.icon,
                "sort": menu.sort,
                "children": build_menu_tree(menus, menu.id),
            }
            tree.append(node)
    return sorted(tree, key=lambda x: x["sort"])


def require_permissions(*permissions):
    """权限检查装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取数据库会话
            db = next(sync_db())
            # 获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # 获取用户权限
            user_permissions = get_user_permissions(current_user, db)

            # 检查是否有所需权限
            if not all(p in user_permissions for p in permissions):
                raise BusinessError(code=ErrorCode.PERMISSION_DENIED, message="没有足够的权限执行此操作")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_roles(*roles):
    """角色检查装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取数据库会话
            db = next(sync_db())
            # 获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # 获取用户信息
            user = db.query(User).filter(User.id == current_user).first()
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # 如果是超级管理员
            if user.is_superuser:
                return await func(*args, **kwargs)

            # 获取用户角色
            user_roles = (
                db.query(Role)
                .filter(Role.id.in_(user.role_ids), Role.status == "active", Role.is_delete == False)
                .all()
            )

            # 检查是否有所需角色
            user_role_codes = [r.code for r in user_roles]
            if not any(r in user_role_codes for r in roles):
                raise BusinessError(code=ErrorCode.ROLE_DENIED, message="没有足够的角色执行此操作")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def data_permission(model: str, field: str = "department_id"):
    """数据权限装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取数据库会话
            db = next(sync_db())
            # 获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # 获取用户信息
            user = db.query(User).filter(User.id == current_user).first()
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # 如果是超级管理员
            if user.is_superuser:
                return await func(*args, **kwargs)

            # 获取用户数据权限范围
            data_scope = get_user_data_scope(user, db)

            # 修改查询条件
            if "filter_args" not in kwargs:
                kwargs["filter_args"] = []

            if data_scope["type"] == "all":
                pass
            elif data_scope["type"] == "custom":
                kwargs["filter_args"].append(f"{model}.{field}.in_({data_scope['departments']})")
            elif data_scope["type"] == "dept":
                kwargs["filter_args"].append(f"{model}.{field} == {user.department_id}")
            elif data_scope["type"] == "dept_and_child":
                dept_ids = get_department_and_children(user.department_id, db)
                kwargs["filter_args"].append(f"{model}.{field}.in_({dept_ids})")
            elif data_scope["type"] == "self":
                kwargs["filter_args"].append(f"{model}.create_by == {current_user}")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def get_user_data_scope(user: User, db: Session) -> dict:
    """获取用户数据权限范围"""
    # 获取用户角色
    roles = (
        db.query(Role)
        .filter(Role.id.in_(user.role_ids), Role.status == "active", Role.is_delete == False)
        .order_by(Role.data_scope.asc())
        .first()
    )

    if not roles:
        return {"type": "self"}

    role = roles[0]
    if role.data_scope == "all":
        return {"type": "all"}
    elif role.data_scope == "custom":
        return {"type": "custom", "departments": role.dept_ids}
    elif role.data_scope == "dept":
        return {"type": "dept"}
    elif role.data_scope == "dept_and_child":
        return {"type": "dept_and_child"}
    else:
        return {"type": "self"}


def get_department_and_children(dept_id: int, db: Session) -> List[int]:
    """获取部门及其子部门ID列表"""
    dept_ids = [dept_id]

    def get_children(parent_id: int):
        children = (
            db.query(Department)
            .filter(Department.parent_id == parent_id, Department.status == "active", Department.is_delete == False)
            .all()
        )
        for child in children:
            dept_ids.append(child.id)
            get_children(child.id)

    get_children(dept_id)
    return dept_ids


# 使用示例:
"""
@router.get("/users")
@require_permissions("user:list")
@require_roles("admin", "manager")
@data_permission("User")
async def list_users(
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user)
):
    # 获取用户列表的业务逻辑
    pass
"""
