from fastapi import APIRouter
from . import users, roles, permissions, menus, departments, configs, logs, cache

# 创建系统管理模块路由
router = APIRouter()

# 注册子路由
router.include_router(users.router, prefix="/users", tags=["用户管理"])
router.include_router(roles.router, prefix="/roles", tags=["角色管理"])
router.include_router(permissions.router, prefix="/permissions", tags=["权限管理"])
router.include_router(menus.router, prefix="/menus", tags=["菜单管理"])
router.include_router(departments.router, prefix="/departments", tags=["部门管理"])
router.include_router(configs.router, prefix="/configs", tags=["系统配置"])
router.include_router(logs.router, prefix="/logs", tags=["系统日志"])
router.include_router(cache.router, prefix="/cache", tags=["缓存管理"]) 