# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：config.py
@Author  ：PySuper
@Date    ：2025/1/2 18:38 
@Desc    ：Speedy config.py
"""
from pydantic import BaseModel

from core.config.load.base import BaseConfig


class AuditConfig(BaseConfig):
    """审计基础配置"""

    log_level: str = "INFO"  # 审计等级
    log_file_path: str = "logs/audit.log"  # 审计记录路径
    AUDIT_LOGGER: str = "logs/audit.log"  # 审计记录路径
    AUDIT_FILE: str = "logs/audit.log"  # 审计记录路径
    AUDIT_LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"  # 审计日志格式
    SENSITIVE_FIELDS: list[str] = []  # 敏感字段
    AUDIT_ENABLED: bool = False  # 是否开启审计功能
