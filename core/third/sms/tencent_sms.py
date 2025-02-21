from typing import Dict, List, Optional, Union

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.sms.v20210111 import models, sms_client

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger
from utils.sms import SMSProvider

logger = get_logger("tencent_sms")


class TencentSMSProvider(SMSProvider):
    """腾讯云短信服务提供者"""

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        region: str = "ap-guangzhou",
        app_id: str = None,
        endpoint: str = "sms.tencentcloudapi.com",
    ):
        # 初始化认证
        cred = credential.Credential(secret_id, secret_key)

        # 初始化配置
        http_profile = HttpProfile()
        http_profile.endpoint = endpoint

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        # 创建客户端
        self.client = sms_client.SmsClient(cred, region, client_profile)

        # 存储配置
        self.app_id = app_id or settings.TENCENT_SMS_APP_ID

    async def send_sms(
        self,
        phone_numbers: Union[str, List[str]],
        template_id: str,
        template_param: Optional[Dict[str, str]] = None,
        sign_name: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """发送短信"""
        try:
            # 处理电话号码
            if isinstance(phone_numbers, str):
                phone_numbers = [phone_numbers]

            # 处理模板参数
            template_param_list = []
            if template_param:
                template_param_list = list(template_param.values())

            # 创建请求
            req = models.SendSmsRequest()
            req.SmsSdkAppId = self.app_id
            req.SignName = sign_name or settings.TENCENT_SMS_SIGN_NAME
            req.TemplateId = template_id
            req.PhoneNumberSet = phone_numbers
            req.TemplateParamSet = template_param_list

            # 发送请求
            response = self.client.SendSms(req)

            # 处理响应
            result = {"request_id": response.RequestId, "send_status_set": []}

            for status in response.SendStatusSet:
                result["send_status_set"].append(
                    {
                        "serial_no": status.SerialNo,
                        "phone_number": status.PhoneNumber,
                        "fee": status.Fee,
                        "session_context": status.SessionContext,
                        "code": status.Code,
                        "message": status.Message,
                        "iso_code": status.IsoCode,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Failed to send SMS via Tencent: {str(e)}")
            raise

    async def send_batch_sms(
        self,
        phone_numbers: List[str],
        template_id: str,
        template_params: List[Dict[str, str]],
        sign_names: Optional[List[str]] = None,
        **kwargs,
    ) -> dict:
        """批量发送短信"""
        try:
            # 处理签名
            if not sign_names:
                sign_names = [settings.TENCENT_SMS_SIGN_NAME] * len(phone_numbers)
            elif len(sign_names) != len(phone_numbers):
                raise ValueError("The length of sign_names must match phone_numbers")

            # 处理模板参数
            if len(template_params) != len(phone_numbers):
                raise ValueError("The length of template_params must match phone_numbers")

            # 创建请求
            req = models.SendSmsRequest()
            req.SmsSdkAppId = self.app_id
            req.SignName = sign_names[0]  # 腾讯云批量发送只支持单个签名
            req.TemplateId = template_id
            req.PhoneNumberSet = phone_numbers
            req.TemplateParamSet = [list(params.values())[0] for params in template_params]

            # 发送请求
            response = self.client.SendSms(req)

            # 处理响应
            result = {"request_id": response.RequestId, "send_status_set": []}

            for status in response.SendStatusSet:
                result["send_status_set"].append(
                    {
                        "serial_no": status.SerialNo,
                        "phone_number": status.PhoneNumber,
                        "fee": status.Fee,
                        "session_context": status.SessionContext,
                        "code": status.Code,
                        "message": status.Message,
                        "iso_code": status.IsoCode,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Failed to send batch SMS via Tencent: {str(e)}")
            raise

    async def query_sms_status(
        self,
        phone_number: str,
        send_date: str,
        biz_id: Optional[str] = None,
        page_size: int = 10,
        page_number: int = 1,
        **kwargs,
    ) -> dict:
        """查询短信发送状态"""
        try:
            # 创建请求
            req = models.PullSmsSendStatusRequest()
            req.SmsSdkAppId = self.app_id
            req.Limit = page_size

            # 发送请求
            response = self.client.PullSmsSendStatus(req)

            # 处理响应
            result = {"request_id": response.RequestId, "pull_callback_status_set": []}

            for status in response.PullCallbackStatusSet:
                result["pull_callback_status_set"].append(
                    {
                        "user_receive_time": status.UserReceiveTime,
                        "nation_code": status.NationCode,
                        "phone_number": status.PhoneNumber,
                        "sign_name": status.SignName,
                        "template_id": status.TemplateId,
                        "serial_no": status.SerialNo,
                        "report_status": status.ReportStatus,
                        "description": status.Description,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Failed to query SMS status via Tencent: {str(e)}")
            raise


# 创建默认腾讯云短信客户端实例
tencent_sms = TencentSMSProvider(
    secret_id=settings.TENCENT_SECRET_ID,
    secret_key=settings.TENCENT_SECRET_KEY,
    region=settings.TENCENT_SMS_REGION,
    app_id=settings.TENCENT_SMS_APP_ID,
    endpoint=settings.TENCENT_SMS_ENDPOINT,
)
