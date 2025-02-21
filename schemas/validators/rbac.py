from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, constr

from models.permission import PermissionType
from models.role import RoleType
from models.user import UserStatus


class Token(BaseModel):
    """令牌模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")
    expires_in: int = Field(3600, description="过期时间(秒)")


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=32, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=64, description="全名")
    phone: Optional[str] = Field(None, max_length=16, description="手机号")
    avatar: Optional[str] = Field(None, max_length=256, description="头像")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    birthday: Optional[datetime] = Field(None, description="生日")
    address: Optional[str] = Field(None, max_length=256, description="地址")
    bio: Optional[str] = Field(None, description="简介")
    department_id: Optional[int] = Field(None, description="部门ID")
    position: Optional[str] = Field(None, max_length=64, description="职位")
    employee_id: Optional[str] = Field(None, max_length=32, description="工号")
    remark: Optional[str] = Field(None, description="备注")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """用户创建模型"""
    password: constr(min_length=8, max_length=128) = Field(..., description="密码")
    status: UserStatus = Field(default=UserStatus.INACTIVE, description="状态")
    is_active: bool = Field(default=True, description="是否激活")
    is_superuser: bool = Field(default=False, description="是否超级管理员")
    is_staff: bool = Field(default=False, description="是否员工")


class UserUpdate(BaseModel):
    """用户更新模型"""
    full_name: Optional[str] = Field(None, max_length=64, description="全名")
    phone: Optional[str] = Field(None, max_length=16, description="手机号")
    avatar: Optional[str] = Field(None, max_length=256, description="头像")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    birthday: Optional[datetime] = Field(None, description="生日")
    address: Optional[str] = Field(None, max_length=256, description="地址")
    bio: Optional[str] = Field(None, description="简介")
    department_id: Optional[int] = Field(None, description="部门ID")
    position: Optional[str] = Field(None, max_length=64, description="职位")
    remark: Optional[str] = Field(None, description="备注")


class UserInDB(UserBase):
    """数据库用户模型"""
    id: int = Field(..., description="用户ID")
    status: UserStatus = Field(..., description="状态")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级管理员")
    is_staff: bool = Field(..., description="是否员工")
    is_verified: bool = Field(..., description="是否验证")
    password_changed_at: Optional[datetime] = Field(None, description="密码修改时间")
    failed_login_count: int = Field(default=0, description="登录失败次数")
    locked_until: Optional[datetime] = Field(None, description="锁定截止时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    last_active: Optional[datetime] = Field(None, description="最后活跃时间")
    last_ip: Optional[str] = Field(None, max_length=50, description="最后登录IP")
    login_count: int = Field(default=0, description="登录次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")



class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., max_length=50, description="角色名称")
    code: str = Field(..., max_length=50, description="角色编码")
    description: Optional[str] = Field(None, description="角色描述")
    type: RoleType = Field(default=RoleType.CUSTOM, description="角色类型")
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")
    menu_ids: List[int] = Field(default_factory=list, description="菜单ID列表")
    data_scope: Optional[str] = Field(None, max_length=50, description="数据权限范围")
    parent_id: Optional[int] = Field(None, description="父级角色ID")
    level: int = Field(default=1, description="层级")
    sort: int = Field(default=0, description="排序号")
    is_active: bool = Field(default=True, description="是否启用")
    is_system: bool = Field(default=False, description="是否系统角色")
    is_default: bool = Field(default=False, description="是否默认角色")
    remark: Optional[str] = Field(None, description="备注")

    model_config = ConfigDict(from_attributes=True)


class RoleCreate(RoleBase):
    """角色创建模型"""
    pass


class RoleUpdate(BaseModel):
    """角色更新模型"""
    name: Optional[str] = Field(None, max_length=50, description="角色名称")
    code: Optional[str] = Field(None, max_length=50, description="角色编码")
    description: Optional[str] = Field(None, description="角色描述")
    type: Optional[RoleType] = Field(None, description="角色类型")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")
    menu_ids: Optional[List[int]] = Field(None, description="菜单ID列表")
    data_scope: Optional[str] = Field(None, max_length=50, description="数据权限范围")
    parent_id: Optional[int] = Field(None, description="父级角色ID")
    level: Optional[int] = Field(None, description="层级")
    sort: Optional[int] = Field(None, description="排序号")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_default: Optional[bool] = Field(None, description="是否默认角色")
    remark: Optional[str] = Field(None, description="备注")


class RoleInDB(RoleBase):
    """数据库角色模型"""
    id: int = Field(..., description="角色ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str = Field(..., max_length=50, description="权限名称")
    code: str = Field(..., max_length=50, description="权限编码")
    description: Optional[str] = Field(None, description="权限描述")
    type: PermissionType = Field(..., description="权限类型")
    parent_id: Optional[int] = Field(None, description="父级权限ID")
    module: str = Field(..., max_length=50, description="所属模块")
    path: Optional[str] = Field(None, max_length=200, description="权限路径")
    method: Optional[str] = Field(None, max_length=20, description="HTTP方法")
    sort: int = Field(default=0, description="排序号")
    is_active: bool = Field(default=True, description="是否启用")
    is_system: bool = Field(default=False, description="是否系统权限")
    is_public: bool = Field(default=False, description="是否公开权限")
    remark: Optional[str] = Field(None, description="备注")

    model_config = ConfigDict(from_attributes=True)


class PermissionCreate(PermissionBase):
    """权限创建模型"""
    pass


class PermissionUpdate(BaseModel):
    """权限更新模型"""
    name: Optional[str] = Field(None, max_length=50, description="权限名称")
    code: Optional[str] = Field(None, max_length=50, description="权限编码")
    description: Optional[str] = Field(None, description="权限描述")
    type: Optional[PermissionType] = Field(None, description="权限类型")
    parent_id: Optional[int] = Field(None, description="父级权限ID")
    module: Optional[str] = Field(None, max_length=50, description="所属模块")
    path: Optional[str] = Field(None, max_length=200, description="权限路径")
    method: Optional[str] = Field(None, max_length=20, description="HTTP方法")
    sort: Optional[int] = Field(None, description="排序号")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_public: Optional[bool] = Field(None, description="是否公开权限")
    remark: Optional[str] = Field(None, description="备注")


class PermissionInDB(PermissionBase):
    """数据库权限模型"""
    id: int = Field(..., description="权限ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserPasswordReset(BaseModel):
    """密码重置模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: constr(min_length=8) = Field(..., description="新密码")


class UserEmailVerify(BaseModel):
    """邮箱验证模型"""
    code: str = Field(..., min_length=6, max_length=6, description="验证码")


class UserPhoneVerify(BaseModel):
    """手机验证模型"""
    code: str = Field(..., min_length=6, max_length=6, description="验证码")


class UserFilter(BaseModel):
    """用户过滤模型"""
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="电子邮箱")
    status: Optional[UserStatus] = Field(None, description="状态")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_superuser: Optional[bool] = Field(None, description="是否超级管理员")
    is_staff: Optional[bool] = Field(None, description="是否员工")
    department_id: Optional[int] = Field(None, description="部门ID")


class UserRoleUpdate(BaseModel):
    """用户角色更新模型"""
    roles: List[int] = Field(default_factory=list, description="角色ID列表")
    is_superuser: Optional[bool] = Field(False, description="是否超级管理员")
    remark: Optional[str] = Field(None, description="备注")


class UserPermissionUpdate(BaseModel):
    """用户权限更新模型"""
    permissions: List[int] = Field(default_factory=list, description="权限ID列表")
    remark: Optional[str] = Field(None, description="备注")


class UserStatusUpdate(BaseModel):
    """用户状态更新模型"""
    status: UserStatus = Field(..., description="状态")
    is_active: bool = Field(True, description="是否激活")
    remark: Optional[str] = Field(None, description="备注")


class PermissionSchema(BaseModel):
    """权限模式类"""
    id: int = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限编码")
    description: Optional[str] = Field(None, description="权限描述")
    type: PermissionType = Field(..., description="权限类型")
    parent_id: Optional[int] = Field(None, description="父级权限ID")
    module: str = Field(..., description="所属模块")
    path: Optional[str] = Field(None, description="权限路径")
    method: Optional[str] = Field(None, description="HTTP方法")
    sort: int = Field(default=0, description="排序号")
    is_active: bool = Field(default=True, description="是否启用")
    is_system: bool = Field(default=False, description="是否系统权限")
    is_public: bool = Field(default=False, description="是否公开权限")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    children: Optional[List["PermissionSchema"]] = Field(default_factory=list, description="子权限列表")

    model_config = ConfigDict(from_attributes=True)


class RoleSchema(BaseModel):
    """角色模式类"""
    id: int = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    code: str = Field(..., description="角色编码")
    description: Optional[str] = Field(None, description="角色描述")
    type: RoleType = Field(..., description="角色类型")
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")
    menu_ids: List[int] = Field(default_factory=list, description="菜单ID列表")
    data_scope: Optional[str] = Field(None, description="数据权限范围")
    parent_id: Optional[int] = Field(None, description="父级角色ID")
    level: int = Field(default=1, description="层级")
    sort: int = Field(default=0, description="排序号")
    is_active: bool = Field(default=True, description="是否启用")
    is_system: bool = Field(default=False, description="是否系统角色")
    is_default: bool = Field(default=False, description="是否默认角色")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    permissions: Optional[List[PermissionSchema]] = Field(default_factory=list, description="权限列表")
    children: Optional[List["RoleSchema"]] = Field(default_factory=list, description="子角色列表")
    user_count: Optional[int] = Field(default=0, description="用户数量")

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    phone: Optional[str] = Field(None, description="手机号")
    avatar: Optional[str] = Field(None, description="头像")
    gender: Optional[str] = Field(None, description="性别")
    birthday: Optional[datetime] = Field(None, description="生日")
    address: Optional[str] = Field(None, description="地址")
    bio: Optional[str] = Field(None, description="简介")
    department_id: Optional[int] = Field(None, description="部门ID")
    position: Optional[str] = Field(None, description="职位")
    employee_id: Optional[str] = Field(None, description="工号")
    status: UserStatus = Field(..., description="状态")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级管理员")
    is_staff: bool = Field(..., description="是否员工")
    is_verified: bool = Field(..., description="是否验证")
    failed_login_count: int = Field(default=0, description="登录失败次数")
    locked_until: Optional[datetime] = Field(None, description="锁定截止时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    last_active: Optional[datetime] = Field(None, description="最后活跃时间")
    last_ip: Optional[str] = Field(None, description="最后登录IP")
    login_count: int = Field(default=0, description="登录次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    roles: Optional[List[RoleSchema]] = Field(default_factory=list, description="角色列表")
    permissions: Optional[List[PermissionSchema]] = Field(default_factory=list, description="权限列表")
    department: Optional[Dict[str, Any]] = Field(None, description="部门信息")
    remark: Optional[str] = Field(None, description="备注")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "Administrator",
                "phone": "13800138000",
                "avatar": "https://example.com/avatar.jpg",
                "status": "active",
                "is_active": True,
                "is_superuser": True,
                "is_staff": True,
                "created_at": "2024-01-01T00:00:00",
                "roles": [
                    {
                        "id": 1,
                        "name": "管理员",
                        "code": "admin",
                        "type": "system"
                    }
                ],
                "permissions": [
                    {
                        "id": 1,
                        "name": "用户管理",
                        "code": "user:manage",
                        "type": "menu"
                    }
                ]
            }
        }
    )

# 解决循环引用
PermissionSchema.model_rebuild()
RoleSchema.model_rebuild()


