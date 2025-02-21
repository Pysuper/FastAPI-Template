import json
from typing import Dict, List, Optional, Union

from alibabacloud_dysmsapi20170525 import models
from alibabacloud_dysmsapi20170525.client import Client
from alibabacloud_tea_openapi.models import Config

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger
from utils.sms import SMSProvider

logger = get_logger("aliyun_sms")


class AliyunSMSProvider(SMSProvider):
    """阿里云短信服务提供者"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        region_id: str = "cn-hangzhou",
        endpoint: str = "dysmsapi.aliyuncs.com",
    ):
        # 初始化配置
        config = Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=region_id,
            endpoint=endpoint,
        )

        # 创建客户端
        self.client = Client(config)

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
            if isinstance(phone_numbers, list):
                phone_numbers = ",".join(phone_numbers)

            # 创建请求
            request = models.SendSmsRequest(
                phone_numbers=phone_numbers,
                sign_name=sign_name or settings.ALIYUN_SMS_SIGN_NAME,
                template_code=template_id,
                template_param=json.dumps(template_param) if template_param else None,
            )

            # 发送请求
            response = self.client.send_sms(request)

            # 处理响应
            result = {
                "request_id": response.body.request_id,
                "message": response.body.message,
                "code": response.body.code,
                "biz_id": response.body.biz_id,
            }

            # 检查发送状态
            if response.body.code != "OK":
                logger.error(f"Failed to send SMS: {response.body.message}")
                raise Exception(f"SMS send failed: {response.body.message}")

            return result

        except Exception as e:
            logger.error(f"Failed to send SMS via Aliyun: {str(e)}")
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
                sign_names = [settings.ALIYUN_SMS_SIGN_NAME] * len(phone_numbers)
            elif len(sign_names) != len(phone_numbers):
                raise ValueError("The length of sign_names must match phone_numbers")

            # 处理模板参数
            if len(template_params) != len(phone_numbers):
                raise ValueError("The length of template_params must match phone_numbers")

            # 创建请求
            request = models.SendBatchSmsRequest(
                phone_numbers_json=json.dumps(phone_numbers),
                sign_names_json=json.dumps(sign_names),
                template_code=template_id,
                template_param_json=json.dumps(template_params),
            )

            # 发送请求
            response = self.client.send_batch_sms(request)

            # 处理响应
            result = {
                "request_id": response.body.request_id,
                "message": response.body.message,
                "code": response.body.code,
                "biz_id": response.body.biz_id,
            }

            # 检查发送状态
            if response.body.code != "OK":
                logger.error(f"Failed to send batch SMS: {response.body.message}")
                raise Exception(f"Batch SMS send failed: {response.body.message}")

            return result

        except Exception as e:
            logger.error(f"Failed to send batch SMS via Aliyun: {str(e)}")
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
            request = models.QuerySendDetailsRequest(
                phone_number=phone_number,
                send_date=send_date,
                page_size=page_size,
                current_page=page_number,
                biz_id=biz_id,
            )

            # 发送请求
            response = self.client.query_send_details(request)

            # 处理响应
            result = {
                "request_id": response.body.request_id,
                "message": response.body.message,
                "code": response.body.code,
                "total_count": response.body.total_count,
                "smsSendDetailDTOs": [],
            }

            # 检查查询状态
            if response.body.code != "OK":
                logger.error(f"Failed to query SMS status: {response.body.message}")
                raise Exception(f"SMS status query failed: {response.body.message}")

            # 处理详细信息
            if response.body.sms_send_detail_d_t_os:
                for detail in response.body.sms_send_detail_d_t_os.sms_send_detail_d_t_o:
                    result["smsSendDetailDTOs"].append(
                        {
                            "phone_num": detail.phone_num,
                            "send_status": detail.send_status,
                            "err_code": detail.err_code,
                            "template_code": detail.template_code,
                            "content": detail.content,
                            "send_date": detail.send_date,
                            "receive_date": detail.receive_date,
                            "out_id": detail.out_id,
                        }
                    )

            return result

        except Exception as e:
            logger.error(f"Failed to query SMS status via Aliyun: {str(e)}")
            raise


# 创建默认阿里云短信客户端实例
aliyun_sms = AliyunSMSProvider(
    access_key_id=settings.ALIYUN_ACCESS_KEY_ID,
    access_key_secret=settings.ALIYUN_ACCESS_KEY_SECRET,
    region_id=settings.ALIYUN_SMS_REGION_ID,
    endpoint=settings.ALIYUN_SMS_ENDPOINT,
)
