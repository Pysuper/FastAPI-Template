# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2024/12/30 10:30 
@Desc    ：Speedy manager.py
"""


class SchemaManager:
    """
    schema管理器
    """

    def __init__(self):
        self.schemas = {}

    def register_schema(self, schema_name, schema_cls):
        self.schemas[schema_name] = schema_cls

    def get_schema(self, schema_name):
        return self.schemas.get(schema_name)

    def get_all_schemas(self):
        return self.schemas

    def clear_schemas(self):
        self.schemas.clear()

    def get_schema_names(self):
        return list(self.schemas.keys())

    def has_schema(self, schema_name):
        return schema_name in self.schemas

    async def close(self):
        pass

    async def init(self, param):
        pass

    async def reload(self, param):
        pass
