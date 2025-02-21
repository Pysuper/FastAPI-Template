# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：email.py
@Author  ：PySuper
@Date    ：2024-12-28 01:18
@Desc    ：Speedy email
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class EmailConfig(BaseModel):
    """邮件配置"""

    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP服务器地址")
    smtp_port: int = Field(default=587, description="SMTP服务器端口")
    username: Optional[str] = Field(default=None, description="SMTP用户名")
    password: Optional[str] = Field(default=None, description="SMTP密码")
    sender: Optional[EmailStr] = Field(default=None, description="发件人邮箱")
    use_tls: bool = Field(default=True, description="是否使用TLS")

    # 邮件默认配置
    default_subject_prefix: str = Field(default="[Speedy]", description="默认邮件主题前缀")
    default_sender_name: str = Field(default="Speedy System", description="默认发件人名称")
    default_charset: str = Field(default="utf-8", description="默认字符集")

    # 重试配置
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_interval: int = Field(default=5, description="重试间隔(秒)")

    # 模板配置
    template_dir: str = Field(default="templates/email", description="邮件模板目录")
    enable_template_cache: bool = Field(default=True, description="是否启用模板缓存")

    # 限流配置
    rate_limit: int = Field(default=100, description="每小时最大发送数")
    burst_limit: int = Field(default=10, description="突发最大发送数")

    class Config:
        env_prefix = "EMAIL_"
        env_file = ".env"

    @property
    def is_configured(self) -> bool:
        """检查是否配置了必要的邮件参数"""
        return all(
            [
                self.smtp_server,
                self.username,
                self.password,
                self.sender,
            ]
        )
