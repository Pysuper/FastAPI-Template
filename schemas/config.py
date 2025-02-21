# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：config.py
@Author  ：PySuper
@Date    ：2024/12/30 17:51 
@Desc    ：Speedy config.py
"""


from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, constr, ConfigDict


class ConfigCreate(BaseModel):
    """创建配置请求模型"""

    name: constr(min_length=2, max_length=50)
    key: constr(min_length=2, max_length=50)
    value: Any
    type: str
    group: str
    description: Optional[str] = None
    is_system: Optional[bool] = False
    remark: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConfigUpdate(BaseModel):
    """更新配置请求模型"""

    name: Optional[str] = None
    value: Optional[Any] = None
    type: Optional[str] = None
    group: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConfigResponse(BaseModel):
    """配置响应模型"""

    id: int
    name: str
    key: str
    value: Any
    type: str
    group: str
    description: Optional[str]
    status: str
    is_system: bool
    remark: Optional[str]
    create_time: datetime
    update_time: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "系统名称",
                "key": "system_name",
                "value": "Speedy",
                "type": "string",
                "group": "system",
                "description": "系统名称配置",
                "status": "active",
                "is_system": True,
                "remark": None,
                "create_time": "2024-01-01T00:00:00",
                "update_time": None,
            }
        },
    )
