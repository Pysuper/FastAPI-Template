# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：__init__.py
@Author  ：PySuper
@Date    ：2025/1/3 12:47 
@Desc    ：Speedy __init__.py
"""

from .auth import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    get_oauth2_scheme,
    oauth2_scheme,
    is_admin,
)

from .db import sync_db, async_db

from .pagination import get_pagination_params

from .permissions import requires_permissions
