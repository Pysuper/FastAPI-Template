# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：message.py
@Author  ：PySuper
@Date    ：2024-12-30 21:12
@Desc    ：Speedy message
"""
from core.db.core.base import AbstractModel


class Message(AbstractModel):
    """
    ���息模型
    """

    __tablename__ = "message"

    id = AbstractModel.Column(AbstractModel.Integer, primary_key=True, autoincrement=True)
    content = AbstractModel.Column(AbstractModel.String(255), nullable=False)
    create_time = AbstractModel.Column(AbstractModel.DateTime, nullable=False)
    user_id = AbstractModel.Column(AbstractModel.Integer, nullable=False)
    is_read = AbstractModel.Column(AbstractModel.Boolean, default=False)

    def __repr__(self):
        return f"<Message(id={self.id}, content={self.content}, create_time={self.create_time}, user_id={self.user_id}, is_read={self.is_read})>"
