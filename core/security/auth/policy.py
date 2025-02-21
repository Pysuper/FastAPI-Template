import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.security.core.base import SecurityBase
from core.security.core.constants import SECURITY_CONSTANTS
from core.security.core.exceptions import PasswordPolicyViolation


class PasswordPolicy(SecurityBase):
    """密码策略"""

    def __init__(self):
        super().__init__()
        self.min_length = SECURITY_CONSTANTS["MIN_PASSWORD_LENGTH"]
        self.max_length = SECURITY_CONSTANTS["MAX_PASSWORD_LENGTH"]
        self.complexity_regex = SECURITY_CONSTANTS["PASSWORD_COMPLEXITY_REGEX"]
        self.history_size = 5  # 密码历史记录大小
        self.max_age = 90  # 密码最大有效期（天）
        self.min_age = 1  # 密码最小有效期（天）
        self._password_history: Dict[str, List[str]] = {}  # 用户ID -> 密码历史
        self._password_changes: Dict[str, datetime] = {}  # 用户ID -> 最后修改时间

    def validate_password(self, password: str, user_id: Optional[str] = None) -> None:
        """验证密码是否符合策略"""
        errors = []

        # 检查长度
        if len(password) < self.min_length:
            errors.append(f"密码长度不能小于{self.min_length}个字符")
        if len(password) > self.max_length:
            errors.append(f"密码长度不能大于{self.max_length}个字符")

        # 检查复杂度
        if not re.match(self.complexity_regex, password):
            errors.append("密码必须包含大小写字母、数字和特殊字符")

        # 检查常见密码
        if self._is_common_password(password):
            errors.append("不能使用常见密码")

        # 检查密码历史
        if user_id and self._is_password_reused(user_id, password):
            errors.append(f"不能重复使用最近{self.history_size}次使用过的密码")

        if errors:
            raise PasswordPolicyViolation(message="密码不符合安全策略", details={"errors": errors})

    def record_password_change(self, user_id: str, password: str) -> None:
        """记录密码变更"""
        # 检查密码最小年龄
        if user_id in self._password_changes:
            last_change = self._password_changes[user_id]
            min_age_date = last_change + timedelta(days=self.min_age)
            if datetime.now() < min_age_date:
                raise PasswordPolicyViolation(
                    message=f"密码修改间隔不能小于{self.min_age}天",
                    details={"last_change": last_change.isoformat(), "next_allowed": min_age_date.isoformat()},
                )

        # 更新密码历史
        if user_id not in self._password_history:
            self._password_history[user_id] = []
        history = self._password_history[user_id]
        history.append(password)
        if len(history) > self.history_size:
            history.pop(0)

        # 更新最后修改时间
        self._password_changes[user_id] = datetime.now()

    def check_password_age(self, user_id: str) -> Optional[Dict[str, Any]]:
        """检查密码年龄"""
        if user_id not in self._password_changes:
            return None

        last_change = self._password_changes[user_id]
        age = (datetime.now() - last_change).days

        if age > self.max_age:
            return {"expired": True, "last_change": last_change.isoformat(), "age_days": age, "max_age": self.max_age}

        return {
            "expired": False,
            "last_change": last_change.isoformat(),
            "age_days": age,
            "max_age": self.max_age,
            "days_until_expiry": self.max_age - age,
        }

    def _is_common_password(self, password: str) -> bool:
        """检查是否是常见密码"""
        common_passwords = {
            "password",
            "123456",
            "qwerty",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "abc123",
            "111111",
            "password123",
        }
        return password.lower() in common_passwords

    def _is_password_reused(self, user_id: str, password: str) -> bool:
        """检查密码是否重复使用"""
        if user_id not in self._password_history:
            return False
        return password in self._password_history[user_id]

    def get_policy_requirements(self) -> Dict[str, Any]:
        """获取密码策略要求"""
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
            "complexity_requirements": [
                "至少包含一个大写字母",
                "至少包含一个小写字母",
                "至少包含一个数字",
                "至少包含一个特殊字符",
            ],
            "history_size": self.history_size,
            "max_age": self.max_age,
            "min_age": self.min_age,
        }
