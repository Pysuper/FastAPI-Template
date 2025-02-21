"""
敏感数据加密服务
实现数据加密和解密功能
"""

import base64
import os
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from security.config.config import SecurityConfig


class EncryptionProvider:
    """加密服务提供者"""

    def __init__(self, config: Optional[SecurityConfig] = None) -> None:
        """
        初始化加密服务

        Args:
            config: 安全配置，如果未提供则使用默认配置
        """
        self.config = config or SecurityConfig()
        self._fernet = None
        self._initialize_fernet()

    def _initialize_fernet(self) -> None:
        """初始化Fernet加密器"""
        if not self.config.ENCRYPTION_KEY:
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
        else:
            key = self.config.ENCRYPTION_KEY.encode()

        self._fernet = Fernet(key)

    async def encrypt(self, value: str) -> str:
        """
        加密数据

        Args:
            value: 要加密的数据

        Returns:
            加密后的数据
        """
        if not value:
            return value

        value_bytes = value.encode()
        encrypted_bytes = self._fernet.encrypt(value_bytes)
        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    async def decrypt(self, encrypted_value: str) -> str:
        """
        解密数据

        Args:
            encrypted_value: 加密的数据

        Returns:
            解密后的数据
        """
        if not encrypted_value:
            return encrypted_value

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception:
            return encrypted_value

    async def encrypt_dict(self, data: Dict[str, Any], sensitive_fields: Optional[set] = None) -> Dict[str, Any]:
        """
        加密字典中的敏感字段

        Args:
            data: 要加密的数据
            sensitive_fields: 敏感字段集合

        Returns:
            加密后的数据
        """
        if not data:
            return data

        encrypted_data = {}
        for key, value in data.items():
            if sensitive_fields and key in sensitive_fields and isinstance(value, str):
                encrypted_data[key] = await self.encrypt(value)
            elif isinstance(value, dict):
                encrypted_data[key] = await self.encrypt_dict(value, sensitive_fields)
            else:
                encrypted_data[key] = value
        return encrypted_data

    async def decrypt_dict(self, data: Dict[str, Any], sensitive_fields: Optional[set] = None) -> Dict[str, Any]:
        """
        解密字典中的敏感字段

        Args:
            data: 加密的数据
            sensitive_fields: 敏感字段集合

        Returns:
            解密后的数据
        """
        if not data:
            return data

        decrypted_data = {}
        for key, value in data.items():
            if sensitive_fields and key in sensitive_fields and isinstance(value, str):
                decrypted_data[key] = await self.decrypt(value)
            elif isinstance(value, dict):
                decrypted_data[key] = await self.decrypt_dict(value, sensitive_fields)
            else:
                decrypted_data[key] = value
        return decrypted_data

    async def init(self) -> None:
        """初始化加密服务"""
        pass

    async def close(self) -> None:
        """关闭加密服务"""
        pass

    async def reload(self, config: Optional[SecurityConfig] = None) -> None:
        """
        重新加载配置

        Args:
            config: 新的配置
        """
        if config:
            self.config = config
            self._initialize_fernet()


class AESEncryption:
    """AES加密实现"""

    def __init__(self, key: bytes):
        self.key = key
        self.backend = default_backend()

    def encrypt(self, data: bytes) -> bytes:
        """
        AES加密

        Args:
            data: 要加密的数据

        Returns:
            (加密后的数据, IV)
        """
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        padded_data = self._pkcs7_pad(data)
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        return iv + encrypted_data

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        AES解密

        Args:
            encrypted_data: 加密的数据

        Returns:
            解密后的数据
        """
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        return self._pkcs7_unpad(padded_data)

    def _pkcs7_pad(self, data: bytes) -> bytes:
        """PKCS7填充"""
        block_size = algorithms.AES.block_size
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding

    def _pkcs7_unpad(self, padded_data: bytes) -> bytes:
        """PKCS7去除填充"""
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]


encryption_provider = EncryptionProvider()
# 导出
__all__ = [
    "EncryptionProvider",
    "encryption_provider",
    "AESEncryption",
]
