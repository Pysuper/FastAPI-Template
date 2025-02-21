# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：manager.py
@Author  ：PySuper
@Date    ：2024/12/30 10:29 
@Desc    ：Speedy manager.py
"""


class ResponseManager:
    """
    响应管理器
    """

    def __init__(self):
        self.response_code = 200
        self.response_message = "Success"
        self.response_data = None

    def set_response_code(self, code):
        self.response_code = code

    def set_response_message(self, message):
        self.response_message = message

    def set_response_data(self, data):
        self.response_data = data

    def get_response(self):
        return {
            "code": self.response_code,
            "message": self.response_message,
            "data": self.response_data,
        }

    def reset(self):
        self.response_code = 200
        self.response_message = "Success"
        self.response_data = None

    async def close(self):
        pass

    async def init(self, param):
        pass

    async def reload(self, param):
        pass
