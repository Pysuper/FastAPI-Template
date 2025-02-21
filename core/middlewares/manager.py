# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2024-12-28 18:33
@Desc    ：中间件管理器

提供中间件的统一管理和配置功能，包括：
    - 中间件注册
    - 中间件配置
    - 中间件排序
    - 中间件加载
"""
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from core.config.setting import settings
from core.middlewares.I18n import I18nMiddleware
from core.middlewares.audit import APIAuditMiddleware
from core.middlewares.auth import AuthMiddleware
from core.middlewares.cache import CacheMiddleware
from core.middlewares.compression import CompressionMiddleware
from core.middlewares.cors import CustomCORSMiddleware
from core.middlewares.encryption import EncryptionMiddleware
from core.middlewares.interceptors import InterceptorMiddleware
from core.middlewares.logging import LoggingMiddleware
from core.middlewares.metrics import MetricsMiddleware, MonitorMiddleware
from core.middlewares.monitor import PerformanceMonitorMiddleware
from core.middlewares.rate_limit import RateLimitMiddleware
from core.middlewares.request import RequestContextMiddleware, RequestLoggingMiddleware
from core.middlewares.security import SecurityMiddleware
from core.middlewares.tracing import TracingMiddleware
from core.security.auth.auth import AuthProvider
from core.loge.manager import logic

# logger = logging.getLogger(__name__)


class MiddlewareManager:
    """中间件管理器"""

    def __init__(self, app: FastAPI) -> None:
        """
        初始化中间件管理器
        :param app: FastAPI应用实例
        """
        self.app = app
        # self.logger = logging.getLogger(__name__)
        self.logger = logic

    def setup(self) -> None:
        """配置中间件"""
        # 基础中间件
        self.app.add_middleware(APIAuditMiddleware) # API审计中间件
        self.app.add_middleware(AuthMiddleware) # 认证中间件
        self.app.add_middleware(CacheMiddleware)    # 缓存中间件
        self.app.add_middleware(CompressionMiddleware)  # TODO: 压缩中间件
        # self.app.add_middleware(CORSMiddleware) # TODO: 跨域中间件
        self.app.add_middleware(CustomCORSMiddleware)   # 自定义CORS中间件
        # self.app.add_middleware(EncryptionMiddleware)   # 加密中间件
        self.app.add_middleware(I18nMiddleware)   # 语言中间件
        self.app.add_middleware(InterceptorMiddleware)   # 拦截器中间件
        self.app.add_middleware(LoggingMiddleware)   # 日志中间件
        self.app.add_middleware(MetricsMiddleware)   # 指标中间件
        self.app.add_middleware(MonitorMiddleware)   # 监控中间件
        self.app.add_middleware(PerformanceMonitorMiddleware)   # 性能监控中间件
        # self.app.add_middleware(RateLimitMiddleware) # 限流中间件
        self.app.add_middleware(RequestContextMiddleware) # 请求上下文中间件
        self.app.add_middleware(RequestLoggingMiddleware) # 请求日志中间件
        self.app.add_middleware(SecurityMiddleware)   # 安全中间件
        # self.app.add_middleware(TracingMiddleware)   # 追踪中间件
        self.app.add_middleware(SecurityMiddleware)  # 安全中间件

        # 加密中间件
        self.app.add_middleware(
            EncryptionMiddleware,
            secret_key=settings.security.SECRET_KEY,
            sensitive_fields=settings.security.SENSITIVE_FIELDS,
            exclude_paths=settings.security.ENCRYPTION_EXCLUDE_PATHS,
        )

        # 认证中间件
        # self.app.add_middleware(AuthMiddleware)

        # CORS中间件
        # self.app.add_middleware(
        #     CORSMiddleware,
        #     allow_origins=settings.cors.allow_origin,
        #     allow_credentials=True,
        #     allow_methods=["*"],
        #     allow_headers=["*"],
        # )

        # 会话中间件
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=settings.security.SECRET_KEY,
            max_age=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        print(" ✅ SessionMiddleware")

        # 可信主机中间件
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.cors.allow_origin,
        )
        print(" ✅ TrustedHostMiddleware")

        # 限流中间件
        if settings.rate_limiter.RATE_LIMIT_ENABLED:
            self.app.add_middleware(
                RateLimitMiddleware,
                max_requests=settings.rate_limiter.RATE_LIMIT_MAX_REQUESTS,
                window=settings.rate_limiter.RATE_LIMIT_WINDOW,
                exclude_paths=settings.rate_limiter.RATE_LIMIT_EXCLUDE_PATHS,
            )
            print(" ✅ RateLimitMiddleware")

        self.logger.info("所有中间件配置成功")


def setup_middlewares(app: FastAPI) -> None:
    """设置中间件"""
    manager = MiddlewareManager(app)
    manager.setup()

# middleware_manager = MiddlewareManager(app)
