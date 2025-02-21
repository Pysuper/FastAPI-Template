# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2024/12/30 10:27 
@Desc    ：Speedy manager.py
"""


class ModelManager:
    """
    模型管理器
    """

    def __init__(self):
        self.models = {}

    def register_model(self, model_name, model_cls):
        """
        注册模型
        :param model_name:
        :param model_cls:
        :return:
        """
        self.models[model_name] = model_cls

    def get_model(self, model_name):
        """
        获取模型
        :param model_name:
        :return:
        """
        return self.models.get(model_name)

    def get_all_models(self):
        """
        获取所有模型
        :return:
        """
        return self.models.values()

    def get_model_names(self):
        """
        获取所有模型名称
        :return:
        """
        return self.models.keys()

    def get_model_by_name(self, model_name):
        """
        根据模型名称获取模型
        :param model_name:
        :return:
        """
        return self.models.get(model_name)

    def get_model_by_cls(self, model_cls):
        """
        根据模型类获取模型
        :param model_cls:
        :return:
        """
        for model_name, cls in self.models.items():
            if cls == model_cls:
                return model_name
        return None

    def delete_model(self, model_name):
        """
        删除模型
        :param model_name:
        :return:
        """
        if model_name in self.models:
            del self.models[model_name]
            return True
        return False

    def update_model(self, model_name, model_cls):
        """
        更新模型
        :param model_name:
        :param model_cls:
        :return:
        """
        if model_name in self.models:
            self.models[model_name] = model_cls
            return True
        return False

    async def close(self):
        pass

    async def init(self, param):
        pass

    async def reload(self, param):
        pass
