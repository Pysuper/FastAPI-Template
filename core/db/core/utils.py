"""
@Project ：Speedy 
@File    ：utils.py
@Author  ：PySuper
@Date    ：2025-01-02 20:59
@Desc    ：数据库工具模块

提供数据库操作的工具函数，包括:
    - 时间戳处理
    - JSON数据处理
    - 事件监听器
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import event


def setup_timestamp_events(model_class: Any) -> None:
    """
    设置时间戳相关的事件监听器
    :param model_class: 模型类
    """

    @event.listens_for(model_class, "before_update", propagate=True)
    def timestamp_before_update(mapper: Any, connection: Any, target: Any) -> None:
        """
        在更新前自动更新时间戳字段
        :param mapper: 映射器
        :param connection: 数据库连接
        :param target: 目标实例
        """
        target.update_time = datetime.now()

    @event.listens_for(model_class, "before_insert", propagate=True)
    def timestamp_before_insert(mapper: Any, connection: Any, target: Any) -> None:
        """
        在插入前自动更新时间戳字段
        :param mapper: 映射器
        :param connection: 数据库连接
        :param target: 目标实例
        """
        target.create_time = datetime.now()
        target.update_time = datetime.now()

        # 处理扩展JSON字段
        if hasattr(target, "ext_json") and target.ext_json:
            target.ext_json = normalize_json(target.ext_json)


def normalize_json(data: Any) -> Any:
    """
    规范化JSON数据
    :param data: 输入数据
    :return: 规范化后的数据
    """
    if isinstance(data, dict):
        return {k: normalize_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_json(v) for v in data]
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, (int, float, str, bool, type(None))):
        return data
    else:
        return str(data)
