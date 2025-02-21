"""
安全管理器模块

提供统一的安全管理功能，包含以下特性：
    1. 用户认证与授权
    2. RBAC权限控制
    3. 密码加密与验证
    4. JWT令牌管理
    5. 权限缓存
    6. 操作审计
    7. SQL注入防护
    8. 请求频率限制

使用示例：
    ```python
    # 初始化
    await security_manager.init()

    # 用户登录
    login_result = await security_manager.login(
        username="user1",
        password="password123",
        extra_fields={"ip": "127.0.0.1"}
    )

    # 检查权限
    has_permission = await security_manager.check_permission(
        permission="user:create",
        user_id="user123"
    )

    # 获取用户信息
    user_info = await security_manager.get_user_info()

    # 加密敏感数据
    encrypted = await security_manager.encrypt_sensitive_data("sensitive_info")

    # 检查SQL注入
    is_safe = await security_manager.check_sql_injection("SELECT * FROM users")

    # 用户登出
    await security_manager.logout()

    # 关闭
    await security_manager.close()
    ```
"""

from typing import Dict, List, Optional, Any, Union

from core.loge.logger import CustomLogger
from security.auth.auth import AuthProvider
from security.auth.password import PasswordManager
from security.auth.permission_audit import AuditLogger
from security.auth.permission_cache import PermissionCacheManager
from security.auth.rbac import RBACManager
from security.config.config import SecurityConfig
from security.core.encryption import EncryptionProvider
from security.core.jw_token import JWTManager
from security.core.rate_limit import RateLimiter
from security.protection.sql_injection import SQLInjectionProtection


class SecurityManager:
    """
    安全管理器
    集成所有安全相关功能的核心类
    """

    def __init__(self, config: Optional[SecurityConfig] = None) -> None:
        """
        初始化安全管理器及其组件

        Args:
            config: 安全配置，如果未提供则使用默认配置
        """
        self.config = config or SecurityConfig()
        self.logger = CustomLogger("security")

        # 初始化各个组件
        self.auth_provider = AuthProvider()
        self.encryption = EncryptionProvider(self.config)
        self.password_manager = PasswordManager()
        self.rbac_manager = RBACManager()
        # 权限缓存和操作审计组件依赖RBAC组件，因此必须初始化RBAC组件后才能初始化
        self.permission_cache = PermissionCacheManager()
        self.audit_logger = AuditLogger()
        self.rate_limiter = RateLimiter(100, 60)
        self.sql_protection = SQLInjectionProtection()
        self.jwt_manager = JWTManager()

        self._current_user: Optional[Dict[str, Any]] = None

    async def init(self) -> None:
        """初始化安全管理器及其所有组件"""
        self.logger.info("Initializing security manager...")
        try:
            await self.auth_provider.init()
            await self.rbac_manager.init()
            await self.permission_cache.init()
            await self.rate_limiter.init()
            self.logger.info("Security manager initialized successfully")
            print(" ✅ SecurityManager")
        except Exception as e:
            self.logger.error(f"Failed to initialize security manager: {str(e)}")
            raise

    async def close(self) -> None:
        """关闭安全管理器及其组件，释放资源"""
        self.logger.info("Shutting down security manager...")
        try:
            if self.auth_provider:
                await self.auth_provider.close()
            if self.permission_cache:
                await self.permission_cache.close()
            if self.rbac_manager:
                await self.rbac_manager.close()
            if self.rate_limiter:
                await self.rate_limiter.close()
            self.logger.info("Security manager shut down successfully")
        except Exception as e:
            self.logger.error(f"Error during security manager shutdown: {str(e)}")
            raise

    async def reload(self, config: Optional[SecurityConfig] = None) -> None:
        """
        重新加载安全管理器配置

        Args:
            config: 新的配置参数
        """
        self.logger.info("Reloading security manager...")
        if config:
            self.config = config
            await self.encryption.reload(config)
            await self.auth_provider.reload(config)
            await self.permission_cache.reload(config)
            await self.rbac_manager.reload(config)
            await self.rate_limiter.reload(config)
        self.logger.info("Security manager reloaded successfully")

    async def login(
        self, username: str, password: str, extra_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码
            extra_fields: 额外的登录字段

        Returns:
            包含用户信息和token的字典

        Raises:
            AuthenticationError: 认证失败
            RateLimitExceeded: 超出登录频率限制
        """
        try:
            # 检查登录频率限制
            if self.config.RATE_LIMIT_ENABLED:
                await self.rate_limiter.check_rate_limit(f"login_{username}")

            # 验证密码
            if not await self.password_manager.verify_password(password, username):
                self.audit_logger.log_failed_login(username)
                raise ValueError("Invalid username or password")

            # 执行登录
            user_info = await self.auth_provider.authenticate(username, password, extra_fields)

            # 生成token
            token = await self.jwt_manager.create_token(user_info)

            # 记录登录审计
            if self.config.AUDIT_ENABLED:
                self.audit_logger.log_successful_login(username)

            self._current_user = user_info
            return {"user": user_info, "token": token}

        except Exception as e:
            self.logger.error(f"Login failed for user {username}: {str(e)}")
            raise

    async def logout(self) -> None:
        """
        用户登出

        记录登出审计并清理相关资源
        """
        if self._current_user:
            try:
                if self.config.AUDIT_ENABLED:
                    self.audit_logger.log_logout(self._current_user["username"])
                await self.jwt_manager.invalidate_token(self._current_user["id"])
                self._current_user = None
            except Exception as e:
                self.logger.error(f"Error during logout: {str(e)}")
                raise

    async def check_permission(self, permission: Union[str, List[str]], user_id: Optional[str] = None) -> bool:
        """
        检查权限

        Args:
            permission: 权限标识或权限列表
            user_id: 用户ID，默认为当前用户

        Returns:
            bool: 是否具有权限
        """
        if not self.config.RBAC_ENABLED:
            return True

        if not user_id and not self._current_user:
            return False

        try:
            user_id = user_id or self._current_user["id"]

            # 首先检查缓存
            cached_result = await self.permission_cache.get_permission(user_id, permission)
            if cached_result is not None:
                return cached_result

            # 检查RBAC权限
            has_permission = await self.rbac_manager.check_permission(user_id, permission)

            # 更新缓存
            await self.permission_cache.set_permission(
                user_id, permission, has_permission, ttl=self.config.RBAC_CACHE_TTL
            )

            # 记录权限检查审计
            if self.config.AUDIT_ENABLED:
                self.audit_logger.log_permission_check(user_id, permission, has_permission)

            return has_permission

        except Exception as e:
            self.logger.error(f"Error checking permission: {str(e)}")
            return False

    async def get_user_info(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取用户信息

        Args:
            user_id: 用户ID，默认为当前用户

        Returns:
            用户信息字典

        Raises:
            ValueError: 未指定用户
        """
        if not user_id and not self._current_user:
            raise ValueError("No user specified")

        try:
            if user_id:
                return await self.auth_provider.get_user_info(user_id)
            return self._current_user
        except Exception as e:
            self.logger.error(f"Error getting user info: {str(e)}")
            raise

    async def get_user_roles(self, user_id: Optional[str] = None) -> List[str]:
        """
        获取用户角色列表

        Args:
            user_id: 用户ID，默认为当前用户

        Returns:
            角色列表
        """
        if not self.config.RBAC_ENABLED:
            return []

        if not user_id and not self._current_user:
            return []

        try:
            user_id = user_id or self._current_user["id"]
            return await self.rbac_manager.get_user_roles(user_id)
        except Exception as e:
            self.logger.error(f"Error getting user roles: {str(e)}")
            return []

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        验证JWT令牌

        Args:
            token: JWT令牌

        Returns:
            解析后的令牌数据
        """
        try:
            return await self.jwt_manager.validate_token(token)
        except Exception as e:
            self.logger.error(f"Token validation failed: {str(e)}")
            raise

    async def encrypt_sensitive_data(self, data: str) -> str:
        """
        加密敏感数据

        Args:
            data: 待加密的数据

        Returns:
            加密后的数据
        """
        try:
            return await self.encryption.encrypt(data)
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise

    async def check_sql_injection(self, sql: str) -> bool:
        """
        检查SQL注入

        Args:
            sql: SQL语句

        Returns:
            是否包含SQL注入风险
        """
        if not self.config.SQL_INJECTION_PROTECTION:
            return False

        try:
            result = await self.sql_protection.check_injection(sql)
            if result and self.config.SQL_INJECTION_LOG:
                self.logger.warning(f"SQL injection attempt detected: {sql}")
            return result
        except Exception as e:
            self.logger.error(f"SQL injection check failed: {str(e)}")
            return True


# 创建全局安全管理器实例
security_manager = SecurityManager()

# 导出
__all__ = [
    "SecurityManager",
    "security_manager",
]
