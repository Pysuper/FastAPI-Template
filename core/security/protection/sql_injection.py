"""
SQL注入防护中间件
实现SQL注入检测和防护
"""

import re
from typing import Dict, List

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.config.manager import config_manager
from core.middlewares.audit import audit_manager


class SQLInjectionProtector:
    """SQL注入检测器"""

    def __init__(self):
        self.config = config_manager.security
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """编译SQL注入检测模式"""
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.config.SQL_INJECTION_PATTERNS]

        # 添加常见的SQL注入模式
        additional_patterns = [
            r"(?:\'|\"|\-\-|\%|\#)",  # 引号和注释
            r"(?i)(?:union\s+all\s+select)",  # UNION查询
            r"(?i)(?:load_file\s*\()",  # 文件操作
            r"(?i)(?:benchmark\s*\(\s*\d+\s*,)",  # 基准测试
            r"(?i)(?:sleep\s*\(\s*\d+\s*\))",  # 延时注入
            r"(?i)(?:\/\*.*\*\/)",  # 内联注释
            r"(?i)(?:into\s+(?:dump|out)file\s*)",  # 文件写入
            r"(?i)(?:group\s+by.+having)",  # GROUP BY注入
            r"(?i)(?:procedure\s+analyse\s*)",  # 存储过程
            r"(?i)(?:;\s*exec\s*\(\s*xp_cmdshell)",  # 命令执行
        ]

        self.patterns.extend([re.compile(pattern) for pattern in additional_patterns])

    def _check_value(self, value: str) -> bool:
        """
        检查单个值是否包含SQL注入
        :param value: 要检查的值
        :return: 是否安全
        """
        return not any(pattern.search(value) for pattern in self.patterns)

    def _check_dict(self, data: Dict) -> bool:
        """
        递归检查字典中的所有值
        :param data: 要检查的字典
        :return: 是否安全
        """
        for value in data.values():
            if isinstance(value, dict):
                if not self._check_dict(value):
                    return False
            elif isinstance(value, (list, set, tuple)):
                if not self._check_sequence(value):
                    return False
            elif isinstance(value, str):
                if not self._check_value(value):
                    return False
        return True

    def _check_sequence(self, data: List) -> bool:
        """
        检查序列中的所有值
        :param data: 要检查的序列
        :return: 是否安全
        """
        for value in data:
            if isinstance(value, dict):
                if not self._check_dict(value):
                    return False
            elif isinstance(value, (list, set, tuple)):
                if not self._check_sequence(value):
                    return False
            elif isinstance(value, str):
                if not self._check_value(value):
                    return False
        return True

    async def check_request(self, request: Request) -> None:
        """
        检查请求中的所有参数
        :param request: 请求对象
        :raises HTTPException: 如果检测到SQL注入
        """
        # 检查查询参数
        query_params = dict(request.query_params)
        if not self._check_dict(query_params):
            await self._log_injection_attempt(request, "query_params")
            raise HTTPException(status_code=400, detail="Potential SQL injection detected in query parameters")

        # 检查请求体
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.json()
                if isinstance(body, dict):
                    if not self._check_dict(body):
                        await self._log_injection_attempt(request, "body")
                        raise HTTPException(status_code=400, detail="Potential SQL injection detected in request body")
            except ValueError:
                pass  # 非JSON请求体，忽略

        # 检查路径参数
        path_params = dict(request.path_params)
        if not self._check_dict(path_params):
            await self._log_injection_attempt(request, "path_params")
            raise HTTPException(status_code=400, detail="Potential SQL injection detected in path parameters")

    async def _log_injection_attempt(self, request: Request, location: str) -> None:
        """
        记录注入尝试
        :param request: 请求对象
        :param location: 注入位置
        """
        user = getattr(request.state, "user", None)
        await audit_manager.log_event(
            event_type="security_violation",
            action="sql_injection_attempt",
            resource=request.url.path,
            user_id=user["id"] if user else None,
            status="blocked",
            metadata={
                "ip": request.client.host,
                "method": request.method,
                "path": request.url.path,
                "location": location,
                "user_agent": request.headers.get("user-agent"),
            },
        )


class SQLInjectionMiddleware(BaseHTTPMiddleware):
    """SQL注入防护中间件"""

    def __init__(self, app):
        super().__init__(app)
        self.protector = SQLInjectionProtector()

    async def dispatch(self, request: Request, call_next):
        # 检查SQL注入
        await self.protector.check_request(request)

        # 继续处理请求
        return await call_next(request)


class SQLInjectionProtection:
    pass
