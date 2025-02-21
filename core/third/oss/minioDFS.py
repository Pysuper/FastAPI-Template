import io
from typing import BinaryIO, Optional, Union

from minio import Minio
from minio.error import S3Error

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger
from utils.storage import StorageProvider

logger = get_logger("minio")


class MinioProvider(StorageProvider):
    """MinIO存储提供者"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = True,
        region: Optional[str] = None,
    ):
        # 初始化客户端
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )

        # 存储配置
        self.bucket = bucket
        self.endpoint = endpoint
        self.secure = secure
        self.base_url = f"{'https' if secure else 'http'}://{endpoint}"

        # 确保bucket存在
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {str(e)}")
            raise

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

            # 获取文件大小
            if hasattr(data, "seek") and hasattr(data, "tell"):
                data.seek(0, io.SEEK_END)
                size = data.tell()
                data.seek(0)
            else:
                size = len(data)

            # 上传文件
            result = self.client.put_object(
                bucket_name=self.bucket,
                object_name=file_path,
                data=data,
                length=size,
                content_type=content_type or "application/octet-stream",
            )

            return f"{self.base_url}/{self.bucket}/{file_path}"

        except Exception as e:
            logger.error(f"Failed to upload file to MinIO: {str(e)}")
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
                self.client.fget_object(
                    bucket_name=self.bucket,
                    object_name=file_path,
                    file_path=local_path,
                )
                return local_path
            else:
                # 下载到内存
                response = self.client.get_object(bucket_name=self.bucket, object_name=file_path)
                return response.read()

        except Exception as e:
            logger.error(f"Failed to download file from MinIO: {str(e)}")
            raise
        finally:
            if "response" in locals():
                response.close()
                response.release_conn()

    async def delete_file(self, file_path: str, **kwargs) -> bool:
        """删除文件"""
        try:
            self.client.remove_object(bucket_name=self.bucket, object_name=file_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from MinIO: {str(e)}")
            raise

    async def get_file_url(self, file_path: str, expires: Optional[int] = None, **kwargs) -> str:
        """获取文件URL"""
        try:
            if expires:
                # 生成带签名的URL
                url = self.client.presigned_get_object(
                    bucket_name=self.bucket,
                    object_name=file_path,
                    expires=expires,
                )
            else:
                # 生成普通URL
                url = f"{self.base_url}/{self.bucket}/{file_path}"
            return url
        except Exception as e:
            logger.error(f"Failed to get file URL from MinIO: {str(e)}")
            raise

    async def get_file_info(self, file_path: str, **kwargs) -> dict:
        """获取文件信息"""
        try:
            stat = self.client.stat_object(bucket_name=self.bucket, object_name=file_path)

            return {
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type,
                "metadata": stat.metadata,
            }
        except Exception as e:
            logger.error(f"Failed to get file info from MinIO: {str(e)}")
            raise

    async def list_files(
        self,
        prefix: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> list:
        """列出文件"""
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket,
                prefix=prefix,
                recursive=True,
            )

            files = []
            count = 0
            for obj in objects:
                if limit and count >= limit:
                    break

                files.append(
                    {
                        "name": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag,
                        "content_type": obj.content_type,
                    }
                )
                count += 1

            return files

        except Exception as e:
            logger.error(f"Failed to list files from MinIO: {str(e)}")
            raise

    async def exists(self, file_path: str, **kwargs) -> bool:
        """检查文��是否存在"""
        try:
            self.client.stat_object(bucket_name=self.bucket, object_name=file_path)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise


# 创建默认MinIO客户端实例
minio_storage = MinioProvider(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    bucket=settings.MINIO_BUCKET,
    secure=settings.MINIO_SECURE,
    region=settings.MINIO_REGION,
)
