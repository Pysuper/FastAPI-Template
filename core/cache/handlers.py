"""
告警处理器模块
"""

import logging
import smtplib
from email.mime.text import MIMEText
from typing import List, Optional

from core.cache.config.monitor import CacheAlert

logger = logging.getLogger(__name__)


class LoggingHandler:
    """日志告警处理器"""

    def __init__(self, logger_name: Optional[str] = None):
        self.logger = logging.getLogger(logger_name or __name__)

    def __call__(self, alert: CacheAlert):
        """处理告警"""
        level = getattr(logging, alert.level.upper(), logging.WARNING)
        self.logger.log(level, f"Cache Alert: [{alert.name}] {alert.message}")


class EmailHandler:
    """邮件告警处理器"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        to_addrs: List[str],
        use_tls: bool = True,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.use_tls = use_tls

    def __call__(self, alert: CacheAlert):
        """处理告警"""
        try:
            # 创建邮件内容
            subject = f"Cache Alert: {alert.name} ({alert.level})"
            body = f"""
            Cache Alert Details:
            -------------------
            Name: {alert.name}
            Level: {alert.level}
            Time: {alert.timestamp}
            Message: {alert.message}
            """

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)

            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")


class WebhookHandler:
    """Webhook告警处理器"""

    def __init__(self, webhook_url: str, timeout: int = 5):
        self.webhook_url = webhook_url
        self.timeout = timeout

    async def __call__(self, alert: CacheAlert):
        """处理告警"""
        try:
            import aiohttp

            payload = {
                "name": alert.name,
                "level": alert.level,
                "message": alert.message,
                "timestamp": alert.timestamp,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload, timeout=self.timeout) as response:
                    if response.status >= 400:
                        logger.error(
                            f"Webhook request failed with status {response.status}: " f"{await response.text()}"
                        )
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")


class CompositeHandler:
    """组合告警处理器"""

    def __init__(self, handlers: List[callable]):
        self.handlers = handlers

    def __call__(self, alert: CacheAlert):
        """处理告警"""
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Handler failed to process alert: {e}")


# 预定义的告警规则
def create_hit_ratio_rule(threshold: float = 0.8, cooldown: int = 300):
    """创建命中率告警规则"""
    return {
        "name": "low_hit_ratio",
        "condition": lambda m: m.get("hit_ratio", 1.0) < threshold,
        "message": f"Cache hit ratio below {threshold:.1%}",
        "level": "warning",
        "cooldown": cooldown,
    }


def create_memory_usage_rule(threshold: float = 0.9, cooldown: int = 300):
    """创建内存使用告警规则"""
    return {
        "name": "high_memory_usage",
        "condition": lambda m: m.get("memory_usage", 0) / m.get("max_size", 1) > threshold,
        "message": f"Cache memory usage above {threshold:.1%}",
        "level": "warning",
        "cooldown": cooldown,
    }


def create_error_rate_rule(threshold: float = 0.1, cooldown: int = 300):
    """创建错误率告警规则"""
    return {
        "name": "high_error_rate",
        "condition": lambda m: (m.get("errors", 0) / max(m.get("total_operations", 1), 1)) > threshold,
        "message": f"Cache error rate above {threshold:.1%}",
        "level": "error",
        "cooldown": cooldown,
    }


class KeyHandler:
    pass


class ErrorHandler:
    pass


class MetricsHandler:
    pass
