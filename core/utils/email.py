import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from core.config.email_config import EmailConfig

# 邮件配置
email_config = EmailConfig()

async def send_email(
    to: str,
    subject: str,
    content: str,
    cc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
) -> bool:
    """发送邮件"""
    try:
        # 创建邮件
        message = MIMEMultipart()
        message["From"] = email_config.sender
        message["To"] = to
        message["Subject"] = subject
        
        if cc:
            message["Cc"] = ", ".join(cc)

        # 添加正文
        message.attach(MIMEText(content, "plain"))

        # 添加附件
        if attachments:
            for file_path in attachments:
                with open(file_path, "rb") as f:
                    part = MIMEText(f.read(), "base64", "utf-8")
                    part["Content-Type"] = "application/octet-stream"
                    part["Content-Disposition"] = f'attachment; filename="{file_path.split("/")[-1]}"'
                    message.attach(part)

        # 发送邮件
        await aiosmtplib.send(
            message,
            hostname=email_config.smtp_server,
            port=email_config.smtp_port,
            username=email_config.username,
            password=email_config.password,
            use_tls=email_config.use_tls,
        )

        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False 