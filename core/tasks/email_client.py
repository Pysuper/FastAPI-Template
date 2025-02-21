# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：email_client.py
@Author  ：PySuper
@Date    ：2024/12/20 13:09 
@Desc    ：Speedy email_client.py
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailClient:
    def __init__(self, host, port, username, password, use_tls, timeout):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout

    def get_template(self, template_id):
        # 这里应该根据 template_id 从某个存储中获取模板内容
        # 模拟一个模板返回
        return Template("Dear {{ name }},\nYour application is {{ status }}.")

    def send(self, message):
        # 连接到 SMTP 服务器
        server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        if self.use_tls:
            server.starttls()
        server.login(self.username, self.password)
        server.send_message(message)
        server.quit()


class Template:
    def __init__(self, template_string):
        self.template_string = template_string

    def render(self, **kwargs):
        from string import Template

        template = Template(self.template_string)
        return template.safe_substitute(**kwargs)


class EmailMessage:
    def __init__(self, subject, body, from_email, to):
        self.subject = subject
        self.body = body
        self.from_email = from_email
        self.to = to

    def as_message(self):
        message = MIMEMultipart()
        message["From"] = self.from_email
        message["To"] = ", ".join(self.to)
        message["Subject"] = self.subject
        message.attach(MIMEText(self.body, "plain"))
        return message
