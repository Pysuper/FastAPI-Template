# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：sms.py
@Author  ：PySuper
@Date    ：2025-01-04 23:30
@Desc    ：Speedy sms
"""
from core.config.load.base import BaseConfig


class SMSConfig(BaseConfig):
    """短信相关配置"""

    SMS_ACCESS_KEY: str = None
    SMS_SECRET_KEY: str = None
    SMS_REGION: str = None
    SMS_SIGN_NAME: str = None
    SMS_TEMPLATE_CODE: str = None
