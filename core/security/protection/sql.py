import re
from typing import Any, Dict, List, Optional, Union

from core.security.core.base import SecurityBase


class SQLInjectionProtector(SecurityBase):
    """SQL注入防护器"""

    # SQL注入特征模式
    INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b.*\b(FROM|INTO|TABLE|DATABASE)\b)",
        r"(--.*$)",  # 单行注释
        r"(/\*.*\*/)",  # 多行注释
        r"(;.*$)",  # 多语句
        r"('.*'.*'.*')",  # 引号嵌套
        r"(#.*$)",  # MySQL注释
        r"(\bOR\b.*\b(TRUE|1=1)\b)",  # OR TRUE/1=1
        r"(\bAND\b.*\b(FALSE|1=0)\b)",  # AND FALSE/1=0
        r"(\bSLEEP\b.*\(\d+\))",  # 时间延迟注入
        r"(\bWAITFOR\b.*DELAY\b)",  # SQL Server时间延迟
        r"(\bBENCHMARK\b.*\(\d+,.*\))",  # MySQL基准测试注入
        r"(\bLIKE\b.*\b[%_])",  # LIKE通配符
    ]

    def __init__(self):
        super().__init__()
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    def check_value(self, value: Any) -> bool:
        """���查单个值是否包含SQL注入"""
        if not isinstance(value, (str, int, float)):
            return True

        value_str = str(value)
        return not any(pattern.search(value_str) for pattern in self._patterns)

    def check_dict(self, data: Dict[str, Any]) -> bool:
        """检查字典中的所有值"""
        for value in data.values():
            if isinstance(value, dict):
                if not self.check_dict(value):
                    return False
            elif isinstance(value, (list, tuple)):
                if not self.check_list(value):
                    return False
            elif not self.check_value(value):
                return False
        return True

    def check_list(self, data: List[Any]) -> bool:
        """检查列表中的所有值"""
        for value in data:
            if isinstance(value, dict):
                if not self.check_dict(value):
                    return False
            elif isinstance(value, (list, tuple)):
                if not self.check_list(value):
                    return False
            elif not self.check_value(value):
                return False
        return True

    def sanitize_value(self, value: Any) -> Any:
        """清理单个值"""
        if not isinstance(value, str):
            return value

        # 转义特殊字符
        value = value.replace("'", "''")
        value = value.replace("\\", "\\\\")
        value = value.replace(";", "")
        value = value.replace("--", "")
        value = value.replace("/*", "")
        value = value.replace("*/", "")
        value = value.replace("#", "")

        return value

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理字典中的所有值"""
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self.sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                result[key] = self.sanitize_list(value)
            else:
                result[key] = self.sanitize_value(value)
        return result

    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """清理列表中的所有值"""
        result = []
        for value in data:
            if isinstance(value, dict):
                result.append(self.sanitize_dict(value))
            elif isinstance(value, (list, tuple)):
                result.append(self.sanitize_list(value))
            else:
                result.append(self.sanitize_value(value))
        return result

    def protect_query(self, query: str, params: Optional[Union[List[Any], Dict[str, Any]]] = None) -> str:
        """保护SQL查询"""
        if not self.check_value(query):
            raise ValueError("SQL查询包含潜在的注入风险")

        if params:
            if isinstance(params, dict):
                if not self.check_dict(params):
                    raise ValueError("SQL参数包含潜在的注入风险")
                params = self.sanitize_dict(params)
            elif isinstance(params, (list, tuple)):
                if not self.check_list(params):
                    raise ValueError("SQL参数包含潜在的注入风险")
                params = self.sanitize_list(params)

        return query
