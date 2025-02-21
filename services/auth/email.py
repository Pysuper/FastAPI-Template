# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：email.py
@Author  ：PySuper
@Date    ：2025/1/3 16:42 
@Desc    ：邮件服务模块

提供系统邮件发送功能，包括：
    - 欢迎邮件
    - 验证码邮件
    - 密码重置邮件
    - 通知邮件
"""

import logging
from typing import Optional

from core.config.setting import settings
from exceptions.third.email import EmailException
from third.email.email import EmailClient

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""

    def __init__(self):
        """初始化邮件客户端"""
        self.client = EmailClient(
            host=settings.email.smtp_server,
            port=settings.smtp_port,
            username=settings.username,
            password=settings.password,
            use_tls=settings.use_tls,
        )

    @classmethod
    async def send_welcome_email(cls, email: str, full_name: str) -> None:
        """发送欢迎邮件

        Args:
            email: 收件人邮箱
            full_name: 收件人姓名

        Raises:
            EmailException: 发送失败时抛出
        """
        try:
            subject = "欢迎加入 Speedy"
            content = f"""
            亲爱的 {full_name}：

            欢迎加入 Speedy！我们很高兴您能成为我们的一员。

            您现在可以使用您的账号登录系统，体验我们提供的各项功能。

            如果您在使用过程中遇到任何问题，请随时联系我们的支持团队。

            祝您使用愉快！

            Speedy 团队
            """
            await cls().client.send_email(to_email=email, subject=subject, content=content, is_html=False)
            logger.info(f"Welcome email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            raise EmailException(f"发送欢迎邮件失败: {str(e)}")

    @classmethod
    async def send_verification_code_email(cls, email: str, full_name: str, code: str) -> None:
        """发送验证码邮件

        Args:
            email: 收件人邮箱
            full_name: 收件人姓名
            code: 验证码

        Raises:
            EmailException: 发送失败时抛出
        """
        try:
            subject = "Speedy 验证码"
            content = f"""
            亲爱的 {full_name}：

            您的验证码是：{code}

            该验证码将在10分钟后失效，请尽快使用。
            如果这不是您本人的操作，请忽略此邮件。

            Speedy 团队
            """
            await cls().client.send_email(to_email=email, subject=subject, content=content, is_html=False)
            logger.info(f"Verification code email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send verification code email to {email}: {str(e)}")
            raise EmailException(f"发送验证码邮件失败: {str(e)}")

    @classmethod
    async def send_password_reset_email(cls, email: str, full_name: str, reset_token: str) -> None:
        """发送密码重置邮件

        Args:
            email: 收件人邮箱
            full_name: 收件人姓名
            reset_token: 重置令牌

        Raises:
            EmailException: 发送失败时抛出
        """
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            subject = "Speedy 密码重置"
            content = f"""
            亲爱的 {full_name}：

            您正在重置密码，请点击下面的链接完成重置：

            {reset_url}

            该链接将在1小时后失效，请尽快处理。
            如果这不是您本人的操作，请忽略此邮件并确保您的账号安全。

            Speedy 团队
            """
            await cls().client.send_email(to_email=email, subject=subject, content=content, is_html=False)
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            raise EmailException(f"发送密码重置邮件失败: {str(e)}")

    @classmethod
    async def send_password_changed_notification(cls, email: str, full_name: str) -> None:
        """发送密码修改通知邮件

        Args:
            email: 收件人邮箱
            full_name: 收件人姓名

        Raises:
            EmailException: 发送失败时抛出
        """
        try:
            subject = "Speedy 密码已修改"
            content = f"""
            亲爱的 {full_name}：

            您的账号密码已经成功修改。

            如果这不是您本人的操作，请立即联系我们的支持团队。

            Speedy 团队
            """
            await cls().client.send_email(to_email=email, subject=subject, content=content, is_html=False)
            logger.info(f"Password changed notification sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send password changed notification to {email}: {str(e)}")
            raise EmailException(f"发送密码修改通知邮件失败: {str(e)}")

    @classmethod
    async def send_security_alert(
        cls, email: str, full_name: str, alert_type: str, details: Optional[str] = None
    ) -> None:
        """发送安全警告邮件

        Args:
            email: 收件人邮箱
            full_name: 收件人姓名
            alert_type: 警告类型
            details: 详细信息

        Raises:
            EmailException: 发送失败时抛出
        """
        try:
            subject = "Speedy 安全警告"
            content = f"""
            亲爱的 {full_name}：

            我们检测到您的账号可能存在安全风险：

            警告类型：{alert_type}
            {f"详细信息：{details}" if details else ""}

            如果这不是您本人的操作，请立即修改密码并联系我们的支持团队。

            Speedy 团队
            """
            await cls().client.send_email(to_email=email, subject=subject, content=content, is_html=False)
            logger.info(f"Security alert sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send security alert to {email}: {str(e)}")
            raise EmailException(f"发送安全警告邮件失败: {str(e)}")
