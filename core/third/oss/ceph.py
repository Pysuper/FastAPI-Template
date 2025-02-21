import io
from typing import BinaryIO, Optional, Union

import boto3
from botocore.client import Config

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger
from utils.storage import StorageProvider

logger = get_logger("ceph")


class CephProvider(StorageProvider):
    """Ceph存储提供者"""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint: str,
        bucket: str,
        secure: bool = True,
        region: str = "",
        signature_version: str = "s3v4",
    ):
        # 初始化配置
        self.endpoint = endpoint
        self.bucket = bucket
        self.secure = secure

        # 创建S3客户端
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=f"{'https' if secure else 'http'}://{endpoint}",
            region_name=region,
            config=Config(signature_version=signature_version),
        )

        # 创建S3资源
        self.resource = boto3.resource(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=f"{'https' if secure else 'http'}://{endpoint}",
            region_name=region,
            config=Config(signature_version=signature_version),
        )

        # 基础URL
        self.base_url = f"{'https' if secure else 'http'}://{endpoint}/{bucket}"

        # 确保bucket存在
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保bucket存在"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except:
            self.client.create_bucket(Bucket=self.bucket)

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
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            # 上传文件
            self.client.upload_fileobj(
                Fileobj=data,
                Bucket=self.bucket,
                Key=file_path,
                ExtraArgs=extra_args,
            )

            return f"{self.base_url}/{file_path}"

        except Exception as e:
            logger.error(f"Failed to upload file to Ceph: {str(e)}")
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
                self.client.download_file(Bucket=self.bucket, Key=file_path, Filename=local_path)
                return local_path
            else:
                # 下载到内存
                response = self.client.get_object(Bucket=self.bucket, Key=file_path)
                return response["Body"].read()

        except Exception as e:
            logger.error(f"Failed to download file from Ceph: {str(e)}")
            raise

    async def delete_file(self, file_path: str, **kwargs) -> bool:
        """删除文件"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Ceph: {str(e)}")
            raise

    async def get_file_url(self, file_path: str, expires: Optional[int] = None, **kwargs) -> str:
        """获取文件URL"""
        try:
            if expires:
                # 生成带签名的URL
                url = self.client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": file_path,
                    },
                    ExpiresIn=expires,
                )
            else:
                # 生成普通URL
                url = f"{self.base_url}/{file_path}"
            return url
        except Exception as e:
            logger.error(f"Failed to get file URL from Ceph: {str(e)}")
            raise

    async def get_file_info(self, file_path: str, **kwargs) -> dict:
        """获取文件信息"""
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=file_path)

            return {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag"),
                "metadata": response.get("Metadata", {}),
            }
        except Exception as e:
            logger.error(f"Failed to get file info from Ceph: {str(e)}")
            raise

    async def list_files(
        self,
        prefix: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> list:
        """列出文件"""
        try:
            paginator = self.client.get_paginator("list_objects_v2")

            params = {"Bucket": self.bucket, "PaginationConfig": {"MaxItems": limit}}

            if prefix:
                params["Prefix"] = prefix

            files = []
            for page in paginator.paginate(**params):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        files.append(
                            {
                                "key": obj["Key"],
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"],
                                "etag": obj["ETag"],
                                "storage_class": obj.get("StorageClass"),
                            }
                        )

            return files

        except Exception as e:
            logger.error(f"Failed to list files from Ceph: {str(e)}")
            raise

    async def exists(self, file_path: str, **kwargs) -> bool:
        """检查文件是否存在"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except:
            return False


# 创建默认Ceph客户端实例
ceph_storage = CephProvider(
    access_key=settings.CEPH_ACCESS_KEY,
    secret_key=settings.CEPH_SECRET_KEY,
    endpoint=settings.CEPH_ENDPOINT,
    bucket=settings.CEPH_BUCKET,
    secure=settings.CEPH_SECURE,
    region=settings.CEPH_REGION,
    signature_version=settings.CEPH_SIGNATURE_VERSION,
)
