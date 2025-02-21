# # -*- coding:utf-8 -*-
# """
# @Project ：Speedy
# @File    ：__init__.py
# @Author  ：PySuper
# @Date    ：2024-12-19 23:08
# @Desc    ：Speedy __init__
# """
#
# """异常处理模块"""
#
# from .base import AppException
# from .codes import ErrorCode
# from .handlers import create_error_response, log_error, setup_exception_handlers
# from .http import (
#     AuthenticationException,
#     BusinessException,
#     CacheException,
#     DatabaseException,
#     FileException,
#     HTTPException,
#     NotFoundException,
#     PermissionException,
#     RateLimitException,
#     SecurityException,
#     ThirdPartyException,
#     ValidationException,
# )
# from .middleware import ExceptionMiddleware, RequestIDMiddleware
# from .utils import (
#     ensure_not_none,
#     handle_exceptions,
#     retry_on_exception,
#     validate_or_raise,
#     wrap_exceptions,
# )
#
# __all__ = [
#     # 基础异常
#     "AppException",
#     "ErrorCode",
#     # HTTP异常
#     "HTTPException",
#     "ValidationException",
#     "AuthenticationException",
#     "PermissionException",
#     "NotFoundException",
#     "DatabaseException",
#     "CacheException",
#     "RateLimitException",
#     "BusinessException",
#     "ThirdPartyException",
#     "SecurityException",
#     "FileException",
#     # 异常处理
#     "create_error_response",
#     "log_error",
#     "setup_exception_handlers",
#     # 中间件
#     "ExceptionMiddleware",
#     "RequestIDMiddleware",
#     # 工具函数
#     "ensure_not_none",
#     "handle_exceptions",
#     "retry_on_exception",
#     "validate_or_raise",
#     "wrap_exceptions",
# ]
