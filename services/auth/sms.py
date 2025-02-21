# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：sms.py
@Author  ：PySuper
@Date    ：2025/1/3 16:43 
@Desc    ：短信服务模块

提供系统短信发送功能，包括：
    - 验证码短信
    - 通知短信
    - 营销短信
    - 警告短信
"""
import logging
from typing import Optional, Dict, Any

from core.config.setting import settings
from exceptions.third.sms import SMSException
from third.sms.sms import SMSClient

logger = logging.getLogger(__name__)


class SMSService:
    """短信服务类"""

    def __init__(self):
        """初始化短信客户端"""
        self.client = SMSClient(
            access_key=settings.sms.SMS_ACCESS_KEY,
            secret_key=settings.sms.SMS_SECRET_KEY,
            region=settings.sms.SMS_REGION,
            sign_name=settings.sms.SMS_SIGN_NAME,
        )

    @classmethod
    async def send_verification_code_sms(cls, phone: str, code: str) -> None:
        """发送验证码短信

        Args:
            phone: 手机号码
            code: 验证码

        Raises:
            SMSException: 发送失败时抛出
        """
        try:
            template_code = "SMS_VERIFY_CODE"
            template_param = {"code": code}
            await cls().client.send_sms(phone_number=phone, template_code=template_code, template_param=template_param)
            logger.info(f"Verification code SMS sent to {phone}")
        except Exception as e:
            logger.error(f"Failed to send verification code SMS to {phone}: {str(e)}")
            raise SMSException(f"发送验证码短信失败: {str(e)}")

    @classmethod
    async def send_login_notification(cls, phone: str, location: str, device: str, time: str) -> None:
        """发送登录通知短信

        Args:
            phone: 手机号码
            location: 登录地点
            device: 登录设备
            time: 登录时间

        Raises:
            SMSException: 发送失败时抛出
        """
        try:
            template_code = "SMS_LOGIN_NOTIFY"
            template_param = {"location": location, "device": device, "time": time}
            await cls().client.send_sms(phone_number=phone, template_code=template_code, template_param=template_param)
            logger.info(f"Login notification SMS sent to {phone}")
        except Exception as e:
            logger.error(f"Failed to send login notification SMS to {phone}: {str(e)}")
            raise SMSException(f"发送登录通知短信失败: {str(e)}")

    @classmethod
    async def send_security_alert_sms(cls, phone: str, alert_type: str, details: Optional[str] = None) -> None:
        """发送安全警告短信

        Args:
            phone: 手机号码
            alert_type: 警告类型
            details: 详细信息

        Raises:
            SMSException: 发送失败时抛出
        """
        try:
            template_code = "SMS_SECURITY_ALERT"
            template_param = {"alert_type": alert_type, "details": details or "未知"}
            await cls().client.send_sms(phone_number=phone, template_code=template_code, template_param=template_param)
            logger.info(f"Security alert SMS sent to {phone}")
        except Exception as e:
            logger.error(f"Failed to send security alert SMS to {phone}: {str(e)}")
            raise SMSException(f"发送安全警告短信失败: {str(e)}")

    @classmethod
    async def send_marketing_sms(
        cls, phone: str, template_code: str, template_param: Dict[str, Any], batch_id: Optional[str] = None
    ) -> None:
        """发送营销短信

        Args:
            phone: 手机号码
            template_code: 模板代码
            template_param: 模板参数
            batch_id: 批次ID

        Raises:
            SMSException: 发送失败时抛出
        """
        try:
            await cls().client.send_sms(
                phone_number=phone, template_code=template_code, template_param=template_param, batch_id=batch_id
            )
            logger.info(f"Marketing SMS sent to {phone}")
        except Exception as e:
            logger.error(f"Failed to send marketing SMS to {phone}: {str(e)}")
            raise SMSException(f"发送营销短信失败: {str(e)}")

    @classmethod
    async def send_batch_sms(
        cls, phones: list[str], template_code: str, template_param: Dict[str, Any], batch_id: Optional[str] = None
    ) -> None:
        """批量发送短信

        Args:
            phones: 手机号码列表
            template_code: 模板代码
            template_param: 模板参数
            batch_id: 批次ID

        Raises:
            SMSException: 发送失败时抛出
        """
        try:
            await cls().client.send_batch_sms(
                phone_numbers=phones, template_code=template_code, template_param=template_param, batch_id=batch_id
            )
            logger.info(f"Batch SMS sent to {len(phones)} phones")
        except Exception as e:
            logger.error(f"Failed to send batch SMS: {str(e)}")
            raise SMSException(f"批量发送短信失败: {str(e)}")

    @classmethod
    async def query_sms_status(cls, phone: str, send_date: str) -> Dict[str, Any]:
        """查询短信发送状态

        Args:
            phone: 手机号码
            send_date: 发送日期(YYYYMMDD)

        Returns:
            短信发送状态信息

        Raises:
            SMSException: 查询失败时抛出
        """
        try:
            status = await cls().client.query_send_status(phone_number=phone, send_date=send_date)
            logger.info(f"SMS status queried for {phone}")
            return status
        except Exception as e:
            logger.error(f"Failed to query SMS status for {phone}: {str(e)}")
            raise SMSException(f"查询短信状态失败: {str(e)}")

    @classmethod
    async def query_sms_template(cls, template_code: str) -> Dict[str, Any]:
        """查询短信模板信息

        Args:
            template_code: 模板代码

        Returns:
            模板信息

        Raises:
            SMSException: 查询失败时抛出
        """
        try:
            template = await cls().client.query_template(template_code)
            logger.info(f"SMS template queried: {template_code}")
            return template
        except Exception as e:
            logger.error(f"Failed to query SMS template {template_code}: {str(e)}")
            raise SMSException(f"查询短信模板失败: {str(e)}")
