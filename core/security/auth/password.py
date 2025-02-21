"""
密码管理模块

提供密码相关的功能：
1. 密码强度验证
2. 密码哈希和验证
3. 密码策略检查
4. 密码历史记录
5. 登录尝试限制
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from security.config.config import SecurityConfig


class PasswordManager:
    """密码管理器"""

    def __init__(self, config: Optional[SecurityConfig] = None) -> None:
        """
        初始化密码管理器

        Args:
            config: 安全配置，如果未提供则使用默认配置
        """
        self.config = config or SecurityConfig()

    async def validate_password(self, password: str, user_id: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        验证密码是否符合策略

        Args:
            password: 待验证的密码
            user_id: 用户ID（用于检查密码历史）

        Returns:
            (是否通过验证, 问题列表)
        """
        issues = []

        # 检查长度
        if len(password) < self.config.PASSWORD_MIN_LENGTH:
            issues.append(f"密码长度不能小于{self.config.PASSWORD_MIN_LENGTH}个字符")

        # 检查大写字母
        if self.config.PASSWORD_REQUIRE_UPPER and not re.search(r"[A-Z]", password):
            issues.append("密码必须包含大写字母")

        # 检查小写字母
        if self.config.PASSWORD_REQUIRE_LOWER and not re.search(r"[a-z]", password):
            issues.append("密码必须包含小写字母")

        # 检查数字
        if self.config.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
            issues.append("密码必须包含数字")

        # 检查特殊字符
        if self.config.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("密码必须包含特殊字符")

        # 如果提供了用户ID，检查密码历史
        if user_id:
            history_issue = await self._check_password_history(password, user_id)
            if history_issue:
                issues.append(history_issue)

        return len(issues) == 0, issues

    async def _check_password_history(self, password: str, user_id: str) -> Optional[str]:
        """
        检查密码历史

        Args:
            password: 密码
            user_id: 用户ID

        Returns:
            错误信息，如果没有问题则返回None
        """
        # TODO: 实现密码历史检查
        return None

    async def check_expiration(self, last_password_change: datetime) -> bool:
        """
        检查密码是否过期

        Args:
            last_password_change: 最后修改密码时间

        Returns:
            是否过期
        """
        if not self.config.PASSWORD_EXPIRE_DAYS:
            return False

        expire_time = last_password_change + timedelta(days=self.config.PASSWORD_EXPIRE_DAYS)
        return datetime.now() >= expire_time

    async def check_login_attempts(self, failed_attempts: int, last_failed_time: Optional[datetime]) -> bool:
        """
        检查登录尝试次数

        Args:
            failed_attempts: 失败次数
            last_failed_time: 最后失败时间

        Returns:
            是否允许登录
        """
        if not self.config.PASSWORD_MAX_ATTEMPTS:
            return True

        if failed_attempts < self.config.PASSWORD_MAX_ATTEMPTS:
            return True

        if not last_failed_time:
            return True

        lock_until = last_failed_time + timedelta(minutes=self.config.PASSWORD_LOCK_DURATION)
        return datetime.now() >= lock_until

    async def hash_password(self, password: str) -> str:
        """
        对密码进行哈希处理

        Args:
            password: 原始密码

        Returns:
            哈希后的密码
        """
        import bcrypt

        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            password: 原始密码
            hashed_password: 哈希后的密码

        Returns:
            验证是否通过
        """
        import bcrypt

        try:
            return bcrypt.checkpw(password.encode(), hashed_password.encode())
        except Exception:
            return False

    async def init(self) -> None:
        """初始化密码管理器"""
        pass

    async def close(self) -> None:
        """关闭密码管理器"""
        pass

    async def reload(self, config: Optional[SecurityConfig] = None) -> None:
        """
        重新加载配置

        Args:
            config: 新的配置
        """
        if config:
            self.config = config


# 导出
__all__ = [
    "PasswordManager",
]
