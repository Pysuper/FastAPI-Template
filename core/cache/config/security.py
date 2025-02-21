"""
安全性增强模块
"""
import base64
import hashlib
import hmac
import os
from typing import Any, Dict, Optional, Set

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from cache.exceptions import EncryptionError, SecurityError, AccessDeniedError
from core.cache.base.interface import CacheBackend


class Encryptor:
    """数据加密器"""

    def __init__(self, key: Optional[str] = None, iterations: int = 100000):
        self.iterations = iterations
        self._fernet = self._create_fernet(key)

    def _create_fernet(self, key: Optional[str]) -> Fernet:
        """创建Fernet实例"""
        if key is None:
            key = base64.urlsafe_b64encode(os.urandom(32))
        elif isinstance(key, str):
            # 使用PBKDF2派生密钥
            salt = b"cache_security"  # 在生产环境中应使用随机salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.iterations,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        """加密数据"""
        try:
            return self._fernet.encrypt(data)
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt(self, data: bytes) -> bytes:
        """解密数据"""
        try:
            return self._fernet.decrypt(data)
        except InvalidToken as e:
            raise EncryptionError(f"Invalid token: {e}")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")


class AccessController:
    """访问控制器"""

    def __init__(self):
        self._acl: Dict[str, Set[str]] = {}  # 键 -> 权限集合
        self._roles: Dict[str, Set[str]] = {}  # 角色 -> 权限集合
        self._user_roles: Dict[str, Set[str]] = {}  # 用户 -> 角色集合

    def add_role(self, role: str, permissions: Set[str]):
        """添加角色"""
        self._roles[role] = set(permissions)

    def add_user_role(self, user: str, role: str):
        """为用户添加角色"""
        if role not in self._roles:
            raise ValueError(f"Role {role} does not exist")
        if user not in self._user_roles:
            self._user_roles[user] = set()
        self._user_roles[user].add(role)

    def set_key_permissions(self, key: str, permissions: Set[str]):
        """设置键的权限要求"""
        self._acl[key] = set(permissions)

    def check_permission(self, user: str, key: str, action: str) -> bool:
        """检查权限

        Args:
            user: 用户标识
            key: 缓存键
            action: 操作类型（read/write）

        Returns:
            bool: 是否有权限
        """
        # 如果键没有ACL，允许访问
        if key not in self._acl:
            return True

        # 获取用户的所有权限
        user_permissions = set()
        for role in self._user_roles.get(user, set()):
            user_permissions.update(self._roles.get(role, set()))

        # 检查是否有所需的权限
        required_permissions = self._acl[key]
        return bool(required_permissions & user_permissions)


class SecureCache(CacheBackend):
    """安全缓存装饰器"""

    def __init__(
        self,
        cache: CacheBackend,
        encryption_key: Optional[str] = None,
        sign_key: Optional[str] = None,
    ):
        self.cache = cache
        self.encryptor = Encryptor(encryption_key) if encryption_key else None
        self.sign_key = sign_key.encode() if sign_key else None
        self.access_controller = AccessController()

    def _sign_data(self, data: bytes) -> bytes:
        """签名数据"""
        if not self.sign_key:
            return data
        signature = hmac.new(self.sign_key, data, hashlib.sha256).digest()
        return signature + data

    def _verify_signature(self, signed_data: bytes) -> bytes:
        """验证签名"""
        if not self.sign_key:
            return signed_data

        signature_size = 32  # SHA256 输出大小
        if len(signed_data) < signature_size:
            raise SecurityError("Data too short to contain signature")

        signature = signed_data[:signature_size]
        data = signed_data[signature_size:]

        expected_signature = hmac.new(self.sign_key, data, hashlib.sha256).digest()

        if not hmac.compare_digest(signature, expected_signature):
            raise SecurityError("Invalid signature")

        return data

    async def get(self, key: str, user: str = "anonymous") -> Optional[Any]:
        """获取值"""
        if not self.access_controller.check_permission(user, key, "read"):
            raise AccessDeniedError(f"User {user} cannot read key {key}")

        value = await self.cache.get(key)
        if value is None:
            return None

        if self.sign_key:
            value = self._verify_signature(value)

        if self.encryptor:
            value = self.encryptor.decrypt(value)

        return value

    async def set(self, key: str, value: Any, expire: Optional[int] = None, user: str = "anonymous") -> bool:
        """设置值"""
        if not self.access_controller.check_permission(user, key, "write"):
            raise AccessDeniedError(f"User {user} cannot write key {key}")

        if self.encryptor:
            value = self.encryptor.encrypt(value)

        if self.sign_key:
            value = self._sign_data(value)

        return await self.cache.set(key, value, expire)

    async def delete(self, key: str, user: str = "anonymous") -> bool:
        """删除值"""
        if not self.access_controller.check_permission(user, key, "write"):
            raise AccessDeniedError(f"User {user} cannot delete key {key}")

        return await self.cache.delete(key)

    # 实现其他必要的方法...
