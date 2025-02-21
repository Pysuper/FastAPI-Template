from typing import List, Optional

from pydantic import Field, validator

from core.config.load.base import BaseConfig


class AppConfig(BaseConfig):
    """应用配置"""

    # 基础配置
    name: str = Field(default="FastAPI App", description="应用名称")
    version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    env: str = Field(default="production", description="运行环境")

    # 项目配置
    prefix: str = Field(default="", description="项目前缀")
    project_name: str = Field(default="FastAPI", description="项目名称")
    description: str = Field(default="FastAPI应用", description="项目描述")
    allowed_hosts: List[str] = Field(default=["*"], description="允许的主机列表")

    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    workers: int = Field(default=1, description="工作进程数")
    reload: bool = Field(default=False, description="是否自动重载")

    # API配置
    api_v1_str: str = Field(default="/api/v1", description="API前缀")
    docs_url: Optional[str] = Field(default="/docs", description="文档URL")
    redoc_url: Optional[str] = Field(default="/redoc", description="ReDoc URL")
    openapi_url: Optional[str] = Field(default="/openapi.json", description="OpenAPI URL")

    # CORS配置
    cors_origins: List[str] = Field(default=["*"], description="CORS允许的源")
    cors_methods: List[str] = Field(default=["*"], description="CORS允许的方法")
    cors_headers: List[str] = Field(default=["*"], description="CORS允许的头部")
    backend_cors_origins: List[str] = Field(default=["*"], description="后端CORS允许的源")

    # 安全配置
    secret_key: str = Field(default="", description="密钥")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间")

    @validator("backend_cors_origins", pre=True)
    def assemble_cors_origins(cls, v: Optional[str | List[str]]) -> List[str]:
        if v is None:
            return ["*"]
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        raise ValueError(f"Invalid CORS origins format: {v}")

    @property
    def fastapi_kwargs(self) -> dict:
        """获取FastAPI初始化参数"""
        return {
            "debug": self.debug,
            "docs_url": self.docs_url,
            "redoc_url": self.redoc_url,
            "openapi_url": self.openapi_url,
            "title": self.name,
            "version": self.version,
            "description": self.description,
        }

    class Config:
        extra = "ignore"
