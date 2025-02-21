import time
import uuid
from typing import Any, Dict, Optional

from fastapi import Request


class RequestContext:
    """
    请求上下文管理器
    """
    
    def __init__(self, request: Request):
        self.request = request
        self.start_time = time.time()
        self._setup_request_state()
        
    def _setup_request_state(self) -> None:
        """设置请求状态"""
        self.request.state.context = self
        self.request.state.start_time = self.start_time
        self.request.state.request_id = self._get_request_id()
        self.request.state.metadata = {}
        
    def _get_request_id(self) -> str:
        """获取或生成请求ID"""
        return self.request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
    @property
    def request_id(self) -> str:
        """获取请求ID"""
        return self.request.state.request_id
        
    @property
    def process_time(self) -> float:
        """获取请求处理时间"""
        return time.time() - self.start_time
        
    @property
    def user(self) -> Optional[Any]:
        """获取当前用户"""
        return getattr(self.request.state, "user", None)
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """获取请求元数据"""
        return self.request.state.metadata
        
    def set_metadata(self, key: str, value: Any) -> None:
        """设置请求元数据"""
        self.metadata[key] = value
        
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取请求元数据"""
        return self.metadata.get(key, default)
        
    @property
    def context_dict(self) -> Dict[str, Any]:
        """获取上下文字典"""
        return {
            "request_id": self.request_id,
            "method": self.request.method,
            "path": self.request.url.path,
            "client_ip": self.request.client.host if self.request.client else None,
            "user_agent": self.request.headers.get("user-agent"),
            "process_time": self.process_time,
            "user_id": getattr(self.user, "id", None) if self.user else None,
            "metadata": self.metadata
        }

class AsyncRequestContext:
    """异步请求上下文管理器"""
    
    def __init__(self, request: Request):
        self.context = RequestContext(request)
        
    async def __aenter__(self) -> RequestContext:
        """进入异步上下文"""
        return self.context
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出异步上下文"""
        # 清理资源或记录日志等
        pass

def get_request_context(request: Request) -> RequestContext:
    """获取请求上下文"""
    if not hasattr(request.state, "context"):
        RequestContext(request)
    return request.state.context
