"""统一的安全中间件实现"""

import re
import time
from typing import Dict, Optional

from fastapi import HTTPException, Request, Response
from pydantic import BaseModel

from core.middlewares.base import BaseCustomMiddleware


class SecurityConfig(BaseModel):
    """安全配置"""
    rate_limit: int = 100  # 每分钟请求限制
    rate_limit_window: int = 60  # 限流窗口(秒)
    enable_sql_injection_check: bool = True
    enable_xss_protection: bool = True
    enable_rate_limit: bool = True
    excluded_paths: list = []


class RateLimiter:
    """请求频率限制器"""
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self._requests: Dict[str, list] = {}
        
    async def check_rate_limit(self, key: str) -> bool:
        now = time.time()
        
        # 获取该key的请求记录
        requests = self._requests.get(key, [])
        
        # 清理过期的请求记录
        requests = [req for req in requests if now - req < self.window]
        
        # 检查是否超过限制
        if len(requests) >= self.limit:
            return False
            
        # 添加新的请求记录
        requests.append(now)
        self._requests[key] = requests
        return True


class SecurityMiddleware(BaseCustomMiddleware):
    """统一安全中间件"""
    
    def __init__(self, app, config: Optional[Dict] = None):
        super().__init__(app)
        self.config = SecurityConfig(**(config or {}))
        self.rate_limiter = RateLimiter(
            self.config.rate_limit,
            self.config.rate_limit_window
        )
        print(" ✅ SecurityMiddleware")
        
    def _should_process(self, request: Request) -> bool:
        """检查是否需要处理该请求"""
        return request.url.path not in self.config.excluded_paths
        
    async def _check_sql_injection(self, request: Request) -> bool:
        """检查SQL注入"""
        if not self.config.enable_sql_injection_check:
            return True
            
        # 简单的SQL注入检测
        sql_patterns = [
            r"(\s|'|\")*((SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)(\s|'|\")*.*)",
            r"(--|\#|\%23).*$",
            r";.*$"
        ]
        
        # 检查请求参数
        params = dict(request.query_params)
        for value in params.values():
            for pattern in sql_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    return False
                    
        return True
        
    def _clean_xss(self, value: str) -> str:
        """清理XSS"""
        if not self.config.enable_xss_protection:
            return value
            
        # 简单的XSS清理
        value = re.sub(r"<script.*?>.*?</script>", "", value, flags=re.IGNORECASE)
        value = re.sub(r"<.*?javascript:.*?>", "", value, flags=re.IGNORECASE)
        value = re.sub(r"<.*?\\s+on\\w+\\s*=.*?>", "", value, flags=re.IGNORECASE)
        return value
        
    async def process_request(self, request: Request) -> None:
        """处理请求"""
        if not self._should_process(request):
            return
            
        # 频率限制检查
        if self.config.enable_rate_limit:
            key = f"{request.client.host}:{request.url.path}"
            if not await self.rate_limiter.check_rate_limit(key):
                raise HTTPException(status_code=429, detail="Too many requests")
                
        # SQL注入检查
        if not await self._check_sql_injection(request):
            raise HTTPException(status_code=403, detail="Potential SQL injection detected")
            
    async def process_response(self, request: Request, response: Response) -> Response:
        """处理响应"""
        if not self._should_process(request):
            return response
            
        # 添加安全响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
