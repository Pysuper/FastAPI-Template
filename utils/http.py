from typing import Any, Dict, Optional, Union

import aiohttp
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential

from core.loge.pysuper_logging import get_logger
from core.strong.circuit_breaker import circuit_breaker

logger = get_logger("http_client")


class HTTPClient:
    """异步HTTP客户端"""

    def __init__(
        self,
        base_url: str = "",
        timeout: int = 30,
        max_retries: int = 3,
        pool_size: int = 100,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector = aiohttp.TCPConnector(limit=pool_size)

    async def init(self):
        """初始化会话"""
        if not self.session:
            self.session = aiohttp.ClientSession(connector=self.connector, timeout=self.timeout)

    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None

    def _build_url(self, path: str) -> str:
        """构建完整URL"""
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    @circuit_breaker(name="http_request")
    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        verify_ssl: bool = True,
        allow_redirects: bool = True,
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        if not self.session:
            await self.init()

        url = self._build_url(path)
        _timeout = ClientTimeout(total=timeout) if timeout else self.timeout

        try:
            async with self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=headers,
                timeout=_timeout,
                verify_ssl=verify_ssl,
                allow_redirects=allow_redirects,
            ) as response:
                # 读取响应内容
                content = await response.read()

                # 尝试解析JSON
                try:
                    result = await response.json()
                except:
                    result = content.decode() if content else None

                # 检查响应状态
                if not response.ok:
                    logger.error(
                        f"HTTP request failed: {response.status} {response.reason}",
                        extra={"url": url, "method": method, "status": response.status, "response": result},
                    )
                    response.raise_for_status()

                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "data": result,
                    "content": content,
                }

        except aiohttp.ClientError as e:
            logger.error(
                f"HTTP request error: {str(e)}",
                extra={
                    "url": url,
                    "method": method,
                    "error": str(e),
                },
            )
            raise

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """GET请求"""
        return await self.request("GET", path, params=params, **kwargs)

    async def post(
        self,
        path: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """POST请求"""
        return await self.request("POST", path, data=data, json_data=json_data, **kwargs)

    async def put(
        self,
        path: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """PUT请求"""
        return await self.request("PUT", path, data=data, json_data=json_data, **kwargs)

    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """DELETE请求"""
        return await self.request("DELETE", path, **kwargs)

    async def patch(
        self,
        path: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """PATCH请求"""
        return await self.request("PATCH", path, data=data, json_data=json_data, **kwargs)

    async def head(self, path: str, **kwargs) -> Dict[str, Any]:
        """HEAD请求"""
        return await self.request("HEAD", path, **kwargs)

    async def options(self, path: str, **kwargs) -> Dict[str, Any]:
        """OPTIONS请求"""
        return await self.request("OPTIONS", path, **kwargs)


# 创建全局HTTP客户端实例
http_client = HTTPClient()
