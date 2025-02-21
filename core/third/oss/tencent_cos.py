import io
from typing import BinaryIO, Optional, Union
from urllib.parse import urljoin

from qcloud_cos import CosConfig, CosS3Client

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger
from utils.storage import StorageProvider

logger = get_logger("tencent_cos")


class TencentCOSProvider(StorageProvider):
    """腾讯云COS存储提供者"""

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        region: str,
        bucket: str,
        scheme: str = "https",
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
    ):
        # 初始化配置
        config = CosConfig(
            Region=region,
            SecretId=secret_id,
            SecretKey=secret_key,
            Token=token,
            Scheme=scheme,
        )

        # 创建客户端
        self.client = CosS3Client(config)

        # 存储配置
        self.bucket = bucket
        self.region = region
        self.scheme = scheme
        self.endpoint = endpoint or f"{bucket}.cos.{region}.myqcloud.com"
        self.base_url = f"{scheme}://{self.endpoint}"

    async def upload_file(
        self,
        file_path: str,
        data: Union[str, bytes, BinaryIO],
        content_type: Optional[str] = None,
        **kwargs,
    ) -> str:
        """上传文件"""
        try:
            # 处理不同类型的数据
            if isinstance(data, str):
                data = data.encode()
            if isinstance(data, bytes):
                data = io.BytesIO(data)

            # 上传参数
            params = {
                "Bucket": self.bucket,
                "Key": file_path,
                "Body": data,
            }

            if content_type:
                params["ContentType"] = content_type

            # 上传文件
            self.client.put_object(**params)

            return urljoin(self.base_url, file_path)

        except Exception as e:
            logger.error(f"Failed to upload file to COS: {str(e)}")
            raise

    async def download_file(
        self,
        file_path: str,
        local_path: Optional[str] = None,
        **kwargs,
    ) -> Union[bytes, str]:
        """下载文件"""
        try:
            if local_path:
                # 下载到本地文件
                response = self.client.get_object(
                    Bucket=self.bucket,
                    Key=file_path,
                )
                response["Body"].get_stream_to_file(local_path)
                return local_path
            else:
                # 下载到内存
                response = self.client.get_object(
                    Bucket=self.bucket,
                    Key=file_path,
                )
                return response["Body"].get_raw_stream().read()

        except Exception as e:
            logger.error(f"Failed to download file from COS: {str(e)}")
            raise

    async def delete_file(self, file_path: str, **kwargs) -> bool:
        """删除文件"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from COS: {str(e)}")
            raise

    async def get_file_url(
        self,
        file_path: str,
        expires: Optional[int] = None,
        **kwargs,
    ) -> str:
        """获取文件URL"""
        try:
            if expires:
                # 生成带签名的URL
                url = self.client.get_presigned_url(
                    Method="GET",
                    Bucket=self.bucket,
                    Key=file_path,
                    Expired=expires,
                )
            else:
                # 生成普通URL
                url = urljoin(self.base_url, file_path)
            return url
        except Exception as e:
            logger.error(f"Failed to get file URL from COS: {str(e)}")
            raise

    async def get_file_info(self, file_path: str, **kwargs) -> dict:
        """获取文件信息"""
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=file_path)

            return {
                "content_type": response["ContentType"],
                "content_length": response["ContentLength"],
                "etag": response["ETag"],
                "last_modified": response["LastModified"],
                "metadata": response.get("Metadata", {}),
            }
        except Exception as e:
            logger.error(f"Failed to get file info from COS: {str(e)}")
            raise

    async def list_files(
        self,
        prefix: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> list:
        """列出文件"""
        try:
            params = {"Bucket": self.bucket, "MaxKeys": limit or 1000}

            if prefix:
                params["Prefix"] = prefix

            response = self.client.list_objects(**params)

            files = []
            if "Contents" in response:
                for item in response["Contents"]:
                    files.append(
                        {
                            "key": item["Key"],
                            "size": item["Size"],
                            "last_modified": item["LastModified"],
                            "etag": item["ETag"],
                            "storage_class": item["StorageClass"],
                        }
                    )
            return files

        except Exception as e:
            logger.error(f"Failed to list files from COS: {str(e)}")
            raise

    async def exists(self, file_path: str, **kwargs) -> bool:
        """检查文件是否存在"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except:
            return False


# 创建默认COS客户端实例
tencent_cos = TencentCOSProvider(
    secret_id=settings.TENCENT_SECRET_ID,
    secret_key=settings.TENCENT_SECRET_KEY,
    region=settings.TENCENT_COS_REGION,
    bucket=settings.TENCENT_COS_BUCKET,
    scheme=settings.TENCENT_COS_SCHEME,
    endpoint=settings.TENCENT_COS_ENDPOINT,
)
