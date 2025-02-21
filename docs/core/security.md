# 安全模块

## 模块简介

安全模块提供了完整的应用安全解决方案，包括身份认证、访问控制、数据加密、安全审计等功能。确保应用系统的安全性、可靠性和合规性。

## 核心功能

1. 身份认证
   - 用户认证
   - JWT令牌
   - OAuth2.0
   - 单点登录
   - 多因素认证

2. 访问控制
   - 角色权限(RBAC)
   - 访问控制列表(ACL)
   - 资源授权
   - 权限验证
   - 动态权限

3. 数据安全
   - 数据加密
   - 密码哈希
   - 敏感数据脱敏
   - 安全传输
   - 数据签名

4. 安全防护
   - XSS防护
   - CSRF防护
   - SQL注入防护
   - 请求限流
   - 防暴力破解

## 使用方法

### 身份认证

```python
from core.security import auth, jwt

# JWT认证
@auth.requires_auth
async def protected_route():
    return {"message": "Protected data"}

# 创建访问令牌
access_token = await jwt.create_access_token(
    data={"sub": user.id},
    expires_delta=timedelta(minutes=30)
)

# 验证令牌
user = await jwt.get_current_user(token)
```

### 访问控制

```python
from core.security import permissions

# 角色装饰器
@permissions.requires_role("admin")
async def admin_only():
    return {"message": "Admin only"}

# 权限装饰器
@permissions.requires_permission("users:write")
async def create_user():
    pass

# 动态权限检查
if await permissions.has_permission(user, "posts:delete", post_id):
    await delete_post(post_id)
```

### 数据加密

```python
from core.security import crypto

# 加密数据
encrypted = await crypto.encrypt_data("sensitive data")

# 解密数据
decrypted = await crypto.decrypt_data(encrypted)

# 密码哈希
hashed_password = await crypto.hash_password("user_password")

# 验证密码
is_valid = await crypto.verify_password("user_password", hashed_password)
```

## 配置选项

```python
SECURITY_CONFIG = {
    "jwt": {
        "secret_key": "your-secret-key",
        "algorithm": "HS256",
        "access_token_expire_minutes": 30,
        "refresh_token_expire_days": 7
    },
    "password": {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True
    },
    "rate_limiting": {
        "enabled": True,
        "max_requests": 100,
        "window_seconds": 60
    },
    "oauth2": {
        "providers": {
            "google": {
                "client_id": "your-client-id",
                "client_secret": "your-client-secret"
            }
        }
    }
}
```

## 最佳实践

1. 认证策略
   - 使用安全的密码策略
   - 实现账户锁定机制
   - 支持多因素认证
   - 定期令牌轮换

2. 权限管理
   - 最小权限原则
   - 职责分离
   - 定期权限审计
   - 权限继承控制

3. 数据保护
   - 敏感数据加密
   - 传输数据加密
   - 安全密钥管理
   - 数据访问审计

## 注意事项

1. 安全配置
   - 安全密钥保护
   - 环境隔离
   - 定期密钥轮换
   - 安全配置审计

2. 性能考虑
   - 缓存认证结果
   - 优化权限检查
   - 合理的令牌过期时间
   - 控制加密开销

3. 合规要求
   - 数据保护法规
   - 安全标准遵循
   - 审计日志保存
   - 隐私保护措施 