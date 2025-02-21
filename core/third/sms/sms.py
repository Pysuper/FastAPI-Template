# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：sms.py
@Author  ：PySuper
@Date    ：2025/1/3 17:00 
@Desc    ：短信客户端模块

提供短信发送的底层实现，包括：
    - 短信配置管理
    - 短信发送客户端
    - 短信模板管理
    - 短信状态查询
"""
import json
import logging
import aiohttp
from typing import Optional, List, Dict, Any, Union

logger = logging.getLogger(__name__)


class SMSConfig:
    """短信配置类"""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
        sign_name: str,
        endpoint: Optional[str] = None,
        timeout: int = 10,
    ):
        """初始化短信配置

        Args:
            access_key: 访问密钥ID
            secret_key: 访问密钥密码
            region: 地域
            sign_name: 短信签名
            endpoint: API端点(可选)
            timeout: 超时时间(秒)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.sign_name = sign_name
        self.endpoint = endpoint or f"https://sms.{region}.aliyuncs.com"
        self.timeout = timeout


class SMSClient:
    """短信客户端类"""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
        sign_name: str,
        endpoint: Optional[str] = None,
        timeout: int = 10,
    ):
        """初始化短信客户端

        Args:
            access_key: 访问密钥ID
            secret_key: 访问密钥密码
            region: 地域
            sign_name: 短信签名
            endpoint: API端点(可选)
            timeout: 超时时间(秒)
        """
        self.config = SMSConfig(
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            sign_name=sign_name,
            endpoint=endpoint,
            timeout=timeout,
        )
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话

        Returns:
            aiohttp.ClientSession: HTTP会话对象
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        return self._session

    async def close(self) -> None:
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def send_sms(
        self,
        phone_number: str,
        template_code: str,
        template_param: Dict[str, Any],
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发送短信

        Args:
            phone_number: 手机号码
            template_code: 模板代码
            template_param: 模板参数
            batch_id: 批次ID(可选)

        Returns:
            发送结果

        Raises:
            Exception: 发送失败时抛出
        """
        try:
            session = await self._get_session()
            params = {
                "PhoneNumbers": phone_number,
                "SignName": self.config.sign_name,
                "TemplateCode": template_code,
                "TemplateParam": json.dumps(template_param),
            }
            if batch_id:
                params["BatchId"] = batch_id

            async with session.post(
                self.config.endpoint + "/SendSms",
                json=params,
                headers=self._get_headers(),
            ) as response:
                result = await response.json()
                if result.get("Code") != "OK":
                    raise Exception(f"发送短信失败: {result.get('Message')}")
                logger.info(f"SMS sent to {phone_number}")
                return result
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            raise
        finally:
            await self.close()

    async def send_batch_sms(
        self,
        phone_numbers: List[str],
        template_code: str,
        template_param: Dict[str, Any],
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """批量发送短信

        Args:
            phone_numbers: 手机号码列表
            template_code: 模板代码
            template_param: 模板参数
            batch_id: 批次ID(可选)

        Returns:
            发送结果

        Raises:
            Exception: 发送失败时抛出
        """
        try:
            session = await self._get_session()
            params = {
                "PhoneNumberJson": json.dumps(phone_numbers),
                "SignNameJson": json.dumps([self.config.sign_name] * len(phone_numbers)),
                "TemplateCode": template_code,
                "TemplateParamJson": json.dumps([template_param] * len(phone_numbers)),
            }
            if batch_id:
                params["BatchId"] = batch_id

            async with session.post(
                self.config.endpoint + "/SendBatchSms",
                json=params,
                headers=self._get_headers(),
            ) as response:
                result = await response.json()
                if result.get("Code") != "OK":
                    raise Exception(f"批量发送短信失败: {result.get('Message')}")
                logger.info(f"Batch SMS sent to {len(phone_numbers)} numbers")
                return result
        except Exception as e:
            logger.error(f"Failed to send batch SMS: {str(e)}")
            raise
        finally:
            await self.close()

    async def query_send_status(
        self,
        phone_number: str,
        send_date: str,
        page_size: int = 10,
        page_number: int = 1,
    ) -> Dict[str, Any]:
        """查询短信发送状态

        Args:
            phone_number: 手机号码
            send_date: 发送日期(YYYYMMDD)
            page_size: 每页记录数
            page_number: 当前页码

        Returns:
            查询结果

        Raises:
            Exception: 查询失败时抛出
        """
        try:
            session = await self._get_session()
            params = {
                "PhoneNumber": phone_number,
                "SendDate": send_date,
                "PageSize": page_size,
                "PageNumber": page_number,
            }

            async with session.get(
                self.config.endpoint + "/QuerySendDetails",
                params=params,
                headers=self._get_headers(),
            ) as response:
                result = await response.json()
                if result.get("Code") != "OK":
                    raise Exception(f"查询发送状态失败: {result.get('Message')}")
                return result
        except Exception as e:
            logger.error(f"Failed to query send status: {str(e)}")
            raise
        finally:
            await self.close()

    async def query_template(self, template_code: str) -> Dict[str, Any]:
        """查询短信模板

        Args:
            template_code: 模板代码

        Returns:
            模板信息

        Raises:
            Exception: 查询失败时抛出
        """
        try:
            session = await self._get_session()
            params = {"TemplateCode": template_code}

            async with session.get(
                self.config.endpoint + "/QuerySmsTemplate",
                params=params,
                headers=self._get_headers(),
            ) as response:
                result = await response.json()
                if result.get("Code") != "OK":
                    raise Exception(f"查询模板失败: {result.get('Message')}")
                return result
        except Exception as e:
            logger.error(f"Failed to query template: {str(e)}")
            raise
        finally:
            await self.close()

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            请求头字典
        """
        # TODO: 实现签名逻辑
        return {
            "Authorization": f"Bearer {self.config.access_key}",
            "Content-Type": "application/json",
        }
