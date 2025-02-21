# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：email.py
@Author  ：PySuper
@Date    ：2025/1/3 16:58 
@Desc    ：邮件客户端模块

提供邮件发送的底层实现，包括：
    - SMTP配置管理
    - 邮件发送客户端
    - 邮件模板管理
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Dict, Any, Union

logger = logging.getLogger(__name__)


class EmailConfig:
    """邮件配置类"""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        timeout: int = 10,
        charset: str = "utf-8",
        default_from: Optional[str] = None,
    ):
        """初始化邮件配置

        Args:
            host: SMTP服务器地址
            port: SMTP服务器端口
            username: 用户名
            password: 密码
            use_tls: 是否使用TLS加密
            timeout: 超时时间(秒)
            charset: 字符编码
            default_from: 默认发件人
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout
        self.charset = charset
        self.default_from = default_from or username


class EmailClient:
    """邮件客户端类"""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        timeout: int = 10,
        charset: str = "utf-8",
        default_from: Optional[str] = None,
    ):
        """初始化邮件客户端

        Args:
            host: SMTP服务器地址
            port: SMTP服务器端口
            username: 用户名
            password: 密码
            use_tls: 是否使用TLS加密
            timeout: 超时时间(秒)
            charset: 字符编码
            default_from: 默认发件人
        """
        self.config = EmailConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            timeout=timeout,
            charset=charset,
            default_from=default_from,
        )
        self._smtp: Optional[smtplib.SMTP] = None

    async def connect(self) -> None:
        """连接SMTP服务器"""
        if self._smtp is not None:
            return

        try:
            if self.config.use_tls:
                self._smtp = smtplib.SMTP(self.config.host, self.config.port, timeout=self.config.timeout)
                self._smtp.starttls()
            else:
                self._smtp = smtplib.SMTP(self.config.host, self.config.port, timeout=self.config.timeout)

            self._smtp.login(self.config.username, self.config.password)
            logger.info("Connected to SMTP server")
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """断开SMTP服务器连接"""
        if self._smtp is not None:
            try:
                self._smtp.quit()
                self._smtp = None
                logger.info("Disconnected from SMTP server")
            except Exception as e:
                logger.error(f"Failed to disconnect from SMTP server: {str(e)}")
                raise

    async def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        content: str,
        from_email: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        is_html: bool = False,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """发送邮件

        Args:
            to_email: 收件人邮箱(单个或列表)
            subject: 邮件主题
            content: 邮件内容
            from_email: 发件人邮箱(可选)
            cc: 抄送人邮箱(可选)
            bcc: 密送人邮箱(可选)
            is_html: 是否为HTML内容
            attachments: 附件列表(可选)，格式为[{"name": "文件名", "content": "文件内容", "type": "文件类型"}]

        Raises:
            Exception: 发送失败时抛出
        """
        try:
            await self.connect()

            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = from_email or self.config.default_from
            msg["To"] = to_email if isinstance(to_email, str) else ", ".join(to_email)

            if cc:
                msg["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)
            if bcc:
                msg["Bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

            # 设置邮件内容
            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(content, content_type, self.config.charset))

            # 添加附件
            if attachments:
                for attachment in attachments:
                    part = MIMEText(attachment["content"], attachment["type"], self.config.charset)
                    part.add_header("Content-Disposition", f"attachment; filename={attachment['name']}")
                    msg.attach(part)

            # 发送邮件
            recipients = []
            if isinstance(to_email, str):
                recipients.append(to_email)
            else:
                recipients.extend(to_email)

            if cc:
                if isinstance(cc, str):
                    recipients.append(cc)
                else:
                    recipients.extend(cc)

            if bcc:
                if isinstance(bcc, str):
                    recipients.append(bcc)
                else:
                    recipients.extend(bcc)

            self._smtp.sendmail(from_addr=msg["From"], to_addrs=recipients, msg=msg.as_string())
            logger.info(f"Email sent to {msg['To']}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise
        finally:
            await self.disconnect()

    async def send_template_email(
        self,
        to_email: Union[str, List[str]],
        template_name: str,
        template_params: Dict[str, Any],
        subject: str,
        from_email: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """发送模板邮件

        Args:
            to_email: 收件人邮箱(单个或列表)
            template_name: 模板名称
            template_params: 模板参数
            subject: 邮件主题
            from_email: 发件人邮箱(可选)
            cc: 抄送人邮箱(可选)
            bcc: 密送人邮箱(可选)
            attachments: 附件列表(可选)

        Raises:
            Exception: 发送失败时抛出
        """
        try:
            # TODO: 实现模板渲染逻辑
            content = f"Template: {template_name}, Params: {template_params}"
            await self.send_email(
                to_email=to_email,
                subject=subject,
                content=content,
                from_email=from_email,
                cc=cc,
                bcc=bcc,
                is_html=True,
                attachments=attachments,
            )
        except Exception as e:
            logger.error(f"Failed to send template email: {str(e)}")
            raise
