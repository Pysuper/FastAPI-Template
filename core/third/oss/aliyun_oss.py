from typing import BinaryIO, Optional, Union
from urllib.parse import urljoin

import oss2

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger
from utils.storage import StorageProvider

logger = get_logger("aliyun_oss")


class AliyunOSSProvider(StorageProvider):
    """阿里云OSS存储提供者"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        bucket_name: str,
        internal: bool = False,
        secure: bool = True,
    ):
        # 初始化OSS客户端
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.internal = internal
        self.secure = secure

        # 创建认证对象
        self.auth = oss2.Auth(access_key_id, access_key_secret)

        # 创建Bucket对象
        endpoint = f"{'https' if secure else 'http'}://{endpoint}"
        if internal:
            endpoint = endpoint.replace(".aliyuncs.com", "-internal.aliyuncs.com")
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)

        # 基础URL
        self.base_url = f"{'https' if secure else 'http'}://{bucket_name}.{endpoint}"

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
            elif hasattr(data, "read"):
                data = data.read()

            # 上传文件
            headers = {}
            if content_type:
                headers["Content-Type"] = content_type

            result = self.bucket.put_object(file_path, data, headers=headers)

            if result.status == 200:
                return urljoin(self.base_url, file_path)
            else:
                raise Exception(f"Upload failed with status: {result.status}")

        except Exception as e:
            logger.error(f"Failed to upload file to OSS: {str(e)}")
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
                result = self.bucket.get_object_to_file(file_path, local_path)
                if result.status == 200:
                    return local_path
            else:
                # 下载到内存
                result = self.bucket.get_object(file_path)
                if result.status == 200:
                    return result.read()

            raise Exception(f"Download failed with status: {result.status}")

        except Exception as e:
            logger.error(f"Failed to download file from OSS: {str(e)}")
            raise

    async def delete_file(self, file_path: str, **kwargs) -> bool:
        """删除文件"""
        try:
            result = self.bucket.delete_object(file_path)
            return result.status == 204
        except Exception as e:
            logger.error(f"Failed to delete file from OSS: {str(e)}")
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
                # 生成带签名��URL
                url = self.bucket.sign_url("GET", file_path, expires)
            else:
                # 生成普通URL
                url = urljoin(self.base_url, file_path)
            return url
        except Exception as e:
            logger.error(f"Failed to get file URL from OSS: {str(e)}")
            raise

    async def get_file_info(self, file_path: str, **kwargs) -> dict:
        """获取文件信息"""
        try:
            result = self.bucket.head_object(file_path)
            if result.status == 200:
                return {
                    "size": result.content_length,
                    "content_type": result.content_type,
                    "last_modified": result.last_modified,
                    "etag": result.etag,
                    "metadata": result.headers.get("x-oss-meta-", {}),
                }
            raise Exception(f"Get info failed with status: {result.status}")
        except Exception as e:
            logger.error(f"Failed to get file info from OSS: {str(e)}")
            raise

    async def list_files(
        self,
        prefix: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> list:
        """列出文件"""
        try:
            files = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix, max_keys=limit):
                files.append(
                    {
                        "name": obj.key,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag,
                        "type": obj.type,
                        "storage_class": obj.storage_class,
                    }
                )
            return files
        except Exception as e:
            logger.error(f"Failed to list files from OSS: {str(e)}")
            raise

    async def exists(self, file_path: str, **kwargs) -> bool:
        """检查文件是否存在"""
        try:
            return self.bucket.object_exists(file_path)
        except Exception as e:
            logger.error(f"Failed to check file existence in OSS: {str(e)}")
            raise


# 创建默认OSS客户端实例
aliyun_oss = AliyunOSSProvider(
    access_key_id=settings.ALIYUN_ACCESS_KEY_ID,
    access_key_secret=settings.ALIYUN_ACCESS_KEY_SECRET,
    endpoint=settings.ALIYUN_OSS_ENDPOINT,
    bucket_name=settings.ALIYUN_OSS_BUCKET,
    internal=settings.ALIYUN_OSS_INTERNAL,
    secure=settings.ALIYUN_OSS_SECURE,
)
