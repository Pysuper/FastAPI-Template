from datetime import datetime
from typing import Any, Dict, Optional

from core.loge.manager import logic


class SecurityBase:
    """基础安全类"""

    def __init__(self):
        self.initialized_at = datetime.now()
        self._config: Dict[str, Any] = {}
        self.logger = logic

    def configure(self, config: Dict[str, Any]) -> None:
        """配置安全选项"""
        self._config.update(config)

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)

    def validate_request(self, request: Any) -> bool:
        """验证请求的基本安全性"""
        raise NotImplementedError

    def audit_log(self, event: str, details: Dict[str, Any]) -> None:
        """记录安全审计日志"""
        raise NotImplementedError

    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        raise NotImplementedError

    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        raise NotImplementedError


class SecurityContext:
    """安全上下文"""

    def __init__(self):
        self.user_id: Optional[str] = None
        self.roles: list[str] = []
        self.permissions: list[str] = []
        self.ip_address: Optional[str] = None
        self.user_agent: Optional[str] = None
        self.session_id: Optional[str] = None
        self.request_id: Optional[str] = None
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "roles": self.roles,
            "permissions": self.permissions,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityContext":
        """从字典创建实例"""
        context = cls()
        context.user_id = data.get("user_id")
        context.roles = data.get("roles", [])
        context.permissions = data.get("permissions", [])
        context.ip_address = data.get("ip_address")
        context.user_agent = data.get("user_agent")
        context.session_id = data.get("session_id")
        context.request_id = data.get("request_id")
        if timestamp := data.get("timestamp"):
            context.timestamp = datetime.fromisoformat(timestamp)
        return context
