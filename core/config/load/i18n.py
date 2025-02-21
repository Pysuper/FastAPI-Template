# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：i18n.py
@Author  ：PySuper
@Date    ：2025-01-04 14:16
@Desc    ：Speedy i18n
"""
from pydantic import BaseModel


class I18NConfig(BaseModel):
    """
    I18N 配置
    """

    default_locale: str = "zh_CN"
    locales: list = ["zh_CN", "en_US"]
    fallback_locale: str = "en_US"
    directory: str = "locales"
    domain: str = "messages"
    locale_path: str = "I18n"
