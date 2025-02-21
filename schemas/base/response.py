from typing import Any, Dict, Generic, Optional, TypeVar, Callable, Union, Awaitable
from starlette.responses import JSONResponse as StarletteJSONResponse, Response as StarletteResponse
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""

    code: int = Field(default=0, description="响应码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")

    class Config:
        json_encoders = {
            # 自定义序列化器
        }


class Response(BaseResponse[T]):
    """响应模型"""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "0",
                "message": "success",
                "data": {
                    "id": 1,
                    "name": "Alice",
                    "age": 20,
                },
            }
        }


class SuccessResponse(BaseResponse[T]):
    """成功响应模型"""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "0",
                "message": "success",
                "data": {
                    "id": 1,
                    "name": "Alice",
                    "age": 20,
                },
            }
        }


class ErrorResponse(BaseResponse[None]):
    """错误响应模型"""

    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "1000",
                "message": "系统内部错误",
                "details": {
                    "error_type": "DatabaseError",
                    "error_location": "user_service.create_user",
                },
            }
        }


class HealthResponse(BaseResponse[Dict[str, Any]]):
    """健康检查响应模型"""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "0",
                "message": "success",
                "data": {
                    "status": "healthy",
                    "version": "1.0.0",
                    "timestamp": "2024-01-20T10:00:00Z",
                },
            }
        }


class JSONResponse(StarletteJSONResponse):
    """JSON响应类

    继承自 Starlette 的 JSONResponse，提供统一的 JSON 响应格式
    """

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[Any] = None,
    ) -> None:
        """
        初始化 JSON 响应

        Args:
            content: 响应内容
            status_code: HTTP 状态码
            headers: 响应头
            media_type: 媒体类型
            background: 后台任务
        """
        # 如果 content 不是标准响应格式，则包装成标准格式
        if not isinstance(content, dict) or not all(key in content for key in ["code", "message", "data"]):
            content = {
                "code": "0" if 200 <= status_code < 300 else str(status_code),
                "message": "success" if 200 <= status_code < 300 else str(content.get("detail", "error")),
                "data": content if 200 <= status_code < 300 else None,
            }

        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


# 中间件请求处理函数类型
RequestResponseEndpoint = Callable[[Request], Awaitable[StarletteResponse]]
