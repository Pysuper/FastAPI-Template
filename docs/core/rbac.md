# RBAC (基于角色的访问控制) 模块

## 模块简介

RBAC模块提供了完整的基于角色的访问控制系统，实现了用户、角色、权限的管理和控制。支持角色继承、动态权限分配、细粒度的访问控制等功能。

## 核心功能

1. 角色管理
   - 角色创建和删除
   - 角色继承关系
   - 角色分配
   - 角色同步
   - 角色层级

2. 权限管理
   - 权限定义
   - 权限分配
   - 权限检查
   - 权限缓存
   - 动态权限

3. 访问控制
   - 资源访问控制
   - 操作权限控制
   - 数据权限控制
   - 接口权限控制
   - 菜单权限控制

4. 安全审计
   - 操作日志
   - 权限变更记录
   - 访问记录
   - 异常检测
   - 安全报告

## 使用方法

### 角色管理

```python
from core.rbac import RoleManager, Role, Permission

# 创建角色
async def create_admin_role():
    role = Role(
        name="admin",
        description="系统管理员",
        permissions=["user:manage", "system:manage"]
    )
    await RoleManager.create_role(role)

# 角色分配
async def assign_role_to_user(user_id: int, role_name: str):
    await RoleManager.assign_role(user_id, role_name)

# 检查用户角色
async def check_user_role(user_id: int, role_name: str):
    return await RoleManager.has_role(user_id, role_name)
```

### 权限控制

```python
from core.rbac import PermissionManager, requires_permission

# 权限检查装饰器
@requires_permission("user:create")
async def create_user(user_data: dict):
    # 创建用户的业务逻辑
    pass

# 动态权限检查
async def update_user(user_id: int, user_data: dict):
    if await PermissionManager.has_permission(
        current_user.id,
        f"user:update:{user_id}"
    ):
        # 更新用户信息
        pass
    else:
        raise PermissionDenied()

# 批量权限检查
async def get_user_permissions(user_id: int):
    permissions = await PermissionManager.get_user_permissions(user_id)
    return permissions
```

### 资源访问控制

```python
from core.rbac import ResourceManager, Resource

# 资源访问控制
class DocumentResource(Resource):
    async def check_access(self, user_id: int, action: str):
        if action == "read":
            return await self.check_read_permission(user_id)
        elif action == "write":
            return await self.check_write_permission(user_id)
        return False

# 使用资源访问控制
doc_resource = DocumentResource(document_id)
if await doc_resource.check_access(user_id, "write"):
    await update_document(document_id, content)
```

## 配置选项

```python
RBAC_CONFIG = {
    "roles": {
        "cache_enabled": True,
        "cache_ttl": 3600,
        "max_inheritance_depth": 5
    },
    "permissions": {
        "case_sensitive": False,
        "delimiter": ":",
        "wildcard_token": "*"
    },
    "resources": {
        "default_policy": "deny",
        "cache_enabled": True
    },
    "audit": {
        "enabled": True,
        "log_level": "INFO",
        "store_days": 90
    }
}
```

## 最佳实践

1. 角色设计
   - 最小权限原则
   - 职责分离
   - 层级管理
   - 动态调整

2. 权限管理
   - 细粒度控制
   - 权限分组
   - 临时权限
   - 权限继承

3. 安全审计
   - 完整日志记录
   - 定期审计
   - 异常检测
   - 报告生成

## 注意事项

1. 性能优化
   - 权限缓存
   - 批量操作
   - 延迟加载
   - 定期清理

2. 安全考虑
   - 权限检查
   - 越权防护
   - 日志记录
   - 敏感操作控制

3. 可维护性
   - 权限命名规范
   - 角色命名规范
   - 文档维护
   - 版本管理 