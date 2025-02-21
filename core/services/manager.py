# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2024/12/30 10:32 
@Desc    ：Speedy manager.py
"""


class ServiceManager:
    """
    第三方服务管理器
    """

    def __init__(self):
        self.services = {}

    def register(self, service_name, service_class):
        """
        注册服务
        :param service_name: 服务名称
        :param service_class: 服务类
        :return:
        """
        self.services[service_name] = service_class

    def get_service(self, service_name):
        """
        获取服务
        :param service_name: 服务名称
        :return: 服务类
        """
        return self.services.get(service_name)

    def start_service(self, service_name):
        """
        启动服务
        :param service_name:
        :return:
        """
        service_class = self.get_service(service_name)
        if service_class:
            service_instance = service_class()
            service_instance.start()
            return service_instance
        else:
            raise Exception(f"Service {service_name} not found")

    def stop_service(self, service_name):
        """
        停止服务
        :param service_name:
        :return:
        """
        service_instance = self.get_service(service_name)
        if service_instance:
            service_instance.stop()
        else:
            raise Exception(f"Service {service_name} not found")

    def restart_service(self, service_name):
        """
        重启服务
        :param service_name:
        :return:
        """
        self.stop_service(service_name)

    def get_service_status(self, service_name):
        """
        获取服务状态
        :param service_name:
        :return:
        """
        service_instance = self.get_service(service_name)
        if service_instance:
            return service_instance.status
        else:
            raise Exception(f"Service {service_name} not found")

    def get_service_info(self, service_name):
        """
        获取服务信息
        :param service_name:
        :return:
        """
        service_instance = self.get_service(service_name)
        if service_instance:
            return service_instance.info
        else:
            raise Exception(f"Service {service_name} not found")

    async def close(self):
        pass

    async def init(self, param):
        pass

    async def reload(self, param):
        pass
