from functools import wraps
from typing import List

from black import Cache
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from core.constants.enums import ResourceType, Action
from core.dependencies import async_db
from core.models import Permission, Role, User_role


class PermissionChecker:
    def __init__(self, db: Session, cache: Cache):
        self.db = db
        self.cache = cache

    async def get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户权限列表"""
        cache_key = f"user_permissions:{user_id}"

        # 尝试从缓存获取
        cached_permissions = await self.cache.get(cache_key)
        if cached_permissions:
            return cached_permissions

        # 从数据库查询
        user_roles = self.db.query(user_role).filter(user_role.c.user_id == user_id).all()
        role_ids = [ur.role_id for ur in user_roles]

        permissions = self.db.query(Permission).join(Role.permissions).filter(Role.id.in_(role_ids)).all()

        permission_codes = [p.code for p in permissions]

        # 存入缓存
        await self.cache.set(cache_key, permission_codes, expire=3600)

        return permission_codes

    def has_permission(self, resource_type: ResourceType, action: Action):
        """权限检查装饰器"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, user=None, db: Session = Depends(async_db), **kwargs):
                if not user:
                    raise HTTPException(status_code=401, detail="未认证")

                required_permission = f"{resource_type}:{action}"
                user_permissions = await self.get_user_permissions(user.id)

                # 检查是否有所需权限
                if required_permission not in user_permissions and "*:*" not in user_permissions:
                    raise HTTPException(status_code=403, detail="权限不足")

                return await func(*args, user=user, db=db, **kwargs)

            return wrapper

        return decorator


# 预定义权限列表
PREDEFINED_PERMISSIONS = [
    # 学生管理权限
    {"code": "student:create", "name": "创建学生", "description": "创建新学生记录"},
    {"code": "student:read", "name": "查看学生", "description": "查看学生信息"},
    {"code": "student:update", "name": "更新学生", "description": "更新学生信息"},
    {"code": "student:delete", "name": "删除学生", "description": "删除学生记录"},
    # 课程管理权限
    {"code": "course:create", "name": "创建课程", "description": "创建新课程"},
    {"code": "course:read", "name": "查看课程", "description": "查看课程信息"},
    {"code": "course:update", "name": "更新课程", "description": "更新课程信息"},
    {"code": "course:delete", "name": "删除课程", "description": "删除课程"},
    # 图书馆管理权限
    {"code": "library:create", "name": "创建资源", "description": "创建新图书资源"},
    {"code": "library:read", "name": "查看资源", "description": "查看图书资源"},
    {"code": "library:update", "name": "更新资源", "description": "更新图书资源"},
    {"code": "library:delete", "name": "删除资源", "description": "删除图书资源"},
    # 考试管理权限
    {"code": "exam:create", "name": "创建考试", "description": "创建新考试"},
    {"code": "exam:read", "name": "查看考试", "description": "查看考试信息"},
    {"code": "exam:update", "name": "更新考试", "description": "更新考试信息"},
    {"code": "exam:delete", "name": "删除考试", "description": "删除考试"},
    # 家长管理权限
    {"code": "parent:create", "name": "创建家长", "description": "创建家长账户"},
    {"code": "parent:read", "name": "查看家长", "description": "查看家长信息"},
    {"code": "parent:update", "name": "更新家长", "description": "更新家长信息"},
    {"code": "parent:delete", "name": "删除家长", "description": "删除家长账户"},
    # 活动管理权限
    {"code": "activity:create", "name": "创建活动", "description": "创建新活动"},
    {"code": "activity:read", "name": "查看活动", "description": "查看活动信息"},
    {"code": "activity:update", "name": "更新活动", "description": "更新活动信息"},
    {"code": "activity:delete", "name": "删除活动", "description": "删除活动"},
    # 超级管理员权限
    {"code": "*:*", "name": "超级管理员", "description": "所有权限"},
]

# 预定义角色列表
PREDEFINED_ROLES = [
    {"name": "超级管理员", "code": "super_admin", "permissions": ["*:*"]},
    {
        "name": "教师",
        "code": "teacher",
        "permissions": [
            "student:read",
            "student:update",
            "course:read",
            "course:update",
            "exam:create",
            "exam:read",
            "exam:update",
            "activity:create",
            "activity:read",
            "activity:update",
        ],
    },
    {"name": "学生", "code": "student", "permissions": ["course:read", "library:read", "exam:read", "activity:read"]},
    {"name": "家长", "code": "parent", "permissions": ["student:read", "course:read", "exam:read", "activity:read"]},
]


async def init_permissions(db: Session):
    """初始化权限和角色"""
    # 创建权限
    for perm in PREDEFINED_PERMISSIONS:
        existing = db.query(Permission).filter_by(code=perm["code"]).first()
        if not existing:
            permission = Permission(code=perm["code"], name=perm["name"], description=perm["description"])
            db.add(permission)

    # 创建角色
    for role_data in PREDEFINED_ROLES:
        existing = db.query(Role).filter_by(code=role_data["code"]).first()
        if not existing:
            role = Role(name=role_data["name"], code=role_data["code"])
            db.add(role)
            db.flush()  # 获取role.id

            # 关联权限
            permissions = db.query(Permission).filter(Permission.code.in_(role_data["permissions"])).all()
            role.permissions.extend(permissions)

    db.commit()
