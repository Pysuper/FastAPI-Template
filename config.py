# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：config.py
@Author  ：PySuper
@Date    ：2024/12/24 16:03 
@Desc    ：Speedy config.py
"""
from core.config.setting import settings

# 通过加载一个.env文件来设置环境变量
setting = settings.get_config(".env")
