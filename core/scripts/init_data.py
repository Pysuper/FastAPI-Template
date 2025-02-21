from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories import permission_repository, role_repository, user_repository
from core.schemas.validators.rbac import PermissionCreate, RoleCreate, UserCreate


async def init_permissions(db: AsyncSession) -> List[str]:
    """初始化权限"""
    permissions = [
        PermissionCreate(name="create_user", description="创建用户", resource="users", action="create"),
        PermissionCreate(name="read_user", description="读取用户信息", resource="users", action="read"),
        PermissionCreate(name="update_user", description="更新用户信息", resource="users", action="update"),
        PermissionCreate(name="delete_user", description="删除用户", resource="users", action="delete"),
        PermissionCreate(name="manage_roles", description="管理角色", resource="roles", action="manage"),
        PermissionCreate(name="manage_permissions", description="管理权限", resource="permissions", action="manage"),
    ]

    created_permissions = await permission_repository.batch_create_permissions(db, permissions=permissions)
    return [p.name for p in created_permissions]


async def init_roles(db: AsyncSession) -> List[str]:
    """初始化角色"""
    roles = [
        RoleCreate(name="admin", description="管理员"),
        RoleCreate(name="user", description="普通用户"),
    ]

    created_roles = []
    for role_in in roles:
        role = await role_repository.create(db, obj_in=role_in)
        created_roles.append(role)

    # 为管理员角色分配所有权限
    admin_role = created_roles[0]
    permissions = await permission_repository.get_multi(db, skip=0, limit=100)
    for perm in permissions[0]:
        await role_repository.add_permission(db, role_id=admin_role.id, permission_id=perm.id)

    # 为普通用户角色分配基本权限
    user_role = created_roles[1]
    basic_permissions = ["read_user"]
    for perm_name in basic_permissions:
        perm = await permission_repository.get_by_name(db, name=perm_name)
        if perm:
            await role_repository.add_permission(db, role_id=user_role.id, permission_id=perm.id)

    return [r.name for r in created_roles]


async def init_superuser(db: AsyncSession) -> None:
    """初始化超级用户"""
    superuser = UserCreate(
        email="admin@example.com",
        username="admin",
        password="admin123",
        full_name="Super Admin",
        is_superuser=True,
        is_active=True,
    )

    user = await user_repository.get_by_email(db, email=superuser.email)
    if not user:
        user = await user_repository.create(db, obj_in=superuser)
        # 分配管理员角色
        admin_role = await role_repository.get_by_name(db, name="admin")
        if admin_role:
            await role_repository.add_user(db, role_id=admin_role.id, user_id=user.id)


async def init(db: AsyncSession) -> None:
    """初始化数据"""
    await init_permissions(db)
    await init_roles(db)
    await init_superuser(db)
