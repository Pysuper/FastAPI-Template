# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：system.py
@Author  ：PySuper
@Date    ：2024/12/24 15:09 
@Desc    ：Speedy system.py
"""

"""
常量定义模块
包含系统中使用的所有常量定义
"""

# 系统常量
SYSTEM_NAME = "ApiRocket"
VERSION = "1.0.0"

# 数据库常量
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# 缓存常量
DEFAULT_CACHE_TTL = 3600  # 默认缓存时间（秒）
MAX_CACHE_SIZE = 1000  # 最大缓存条目数

# 安全常量
TOKEN_EXPIRE_MINUTES = 60 * 24  # token过期时间（分钟）
PASSWORD_MIN_LENGTH = 8  # 密码最小长度

# 文件上传常量
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 最大上传文件大小（10MB）
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx"}

# API常量
API_V1_PREFIX = "/api/v1"
API_V2_PREFIX = "/api/v2"
