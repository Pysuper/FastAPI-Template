from datetime import datetime, timedelta
from typing import Any, Optional, Union
from jose import jwt
from passlib.context import CryptContext

from core.config.setting import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """安全管理器"""

    def __init__(self, secret_key: str = settings.SECRET_KEY):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(self, subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)

    def decode_token(self, token: str) -> Optional[str]:
        """解码令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("sub")
        except jwt.JWTError:
            return None


class PermissionManager:
    """权限管理器"""

    @staticmethod
    def has_permission(user: Any, permission: str) -> bool:
        """检查用户是否有指定权限"""
        if not user or not user.permissions:
            return False
        return permission in user.permissions

    @staticmethod
    def has_role(user: Any, role: str) -> bool:
        """检查用户是否有指定角色"""
        if not user or not user.roles:
            return False
        return role in user.roles

    @staticmethod
    def get_user_permissions(user: Any) -> list:
        """获取用户所有权限"""
        if not user:
            return []
        permissions = set()
        # 添加用户直接权限
        if user.permissions:
            permissions.update(user.permissions)
        # 添加角色权限
        if user.roles:
            for role in user.roles:
                if role.permissions:
                    permissions.update(role.permissions)
        return list(permissions)
