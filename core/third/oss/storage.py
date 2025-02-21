"""
文件存储管理器
实现文件的上传、存储和管理
"""

import asyncio
import hashlib
import logging
import mimetypes
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional, Union
from urllib.parse import urljoin

import aiofiles
from PIL import Image
from fastapi import UploadFile

from core.config.manager import config_manager
from core.strong.event_bus import Event, event_bus
from core.strong.metrics import metrics_collector

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """存储错误"""

    pass


class FileInfo:
    """文件信息"""

    def __init__(
        self,
        filename: str,
        content_type: str,
        size: int,
        path: str,
        url: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        self.filename = filename
        self.content_type = content_type
        self.size = size
        self.path = path
        self.url = url
        self.metadata = metadata or {}
        self.created_at = datetime.now()

    @property
    def extension(self) -> str:
        """获取文件扩展名"""
        return os.path.splitext(self.filename)[1].lower()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
            "path": self.path,
            "url": self.url,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class StorageBackend(ABC):
    """存储后端基类"""

    @abstractmethod
    async def save(
        self, file: Union[UploadFile, BinaryIO, bytes], path: str, content_type: Optional[str] = None
    ) -> FileInfo:
        """
        保存文件
        :param file: 文件对象
        :param path: 存储路径
        :param content_type: 内容类型
        :return: 文件信息
        """
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """
        删除文件
        :param path: 文件路径
        :return: 是否成功
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        检查文件是否存在
        :param path: 文件路径
        :return: 是否存在
        """
        pass

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """
        获取文件URL
        :param path: 文件路径
        :return: 文件URL
        """
        pass

    @abstractmethod
    async def get_info(self, path: str) -> Optional[FileInfo]:
        """
        获取文件信息
        :param path: 文件路径
        :return: 文件信息
        """
        pass


class LocalStorageBackend(StorageBackend):
    """本地文件存储后端"""

    def __init__(self, root_path: str, base_url: str):
        self.root_path = Path(root_path)
        self.base_url = base_url.rstrip("/")
        self._ensure_dir(self.root_path)

    def _ensure_dir(self, path: Path) -> None:
        """确保目录存在"""
        if not path.exists():
            path.mkdir(parents=True)

    async def save(
        self, file: Union[UploadFile, BinaryIO, bytes], path: str, content_type: Optional[str] = None
    ) -> FileInfo:
        """保存文件"""
        file_path = self.root_path / path
        self._ensure_dir(file_path.parent)

        try:
            if isinstance(file, UploadFile):
                content = await file.read()
                size = len(content)
                content_type = content_type or file.content_type
            elif isinstance(file, bytes):
                content = file
                size = len(content)
                content_type = content_type or mimetypes.guess_type(path)[0]
            else:
                content = file.read()
                size = len(content)
                content_type = content_type or mimetypes.guess_type(path)[0]

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            url = urljoin(self.base_url, path)

            return FileInfo(filename=os.path.basename(path), content_type=content_type, size=size, path=path, url=url)

        except Exception as e:
            logger.error(f"Failed to save file: {path}", exc_info=e)
            raise StorageError(f"Failed to save file: {str(e)}")

    async def delete(self, path: str) -> bool:
        """删除文件"""
        file_path = self.root_path / path
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file: {path}", exc_info=e)
            return False

    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return (self.root_path / path).exists()

    async def get_url(self, path: str) -> str:
        """获取文件URL"""
        return urljoin(self.base_url, path)

    async def get_info(self, path: str) -> Optional[FileInfo]:
        """获取文件信息"""
        file_path = self.root_path / path
        if not file_path.exists():
            return None

        try:
            size = file_path.stat().st_size
            content_type = mimetypes.guess_type(path)[0]
            url = urljoin(self.base_url, path)

            return FileInfo(filename=os.path.basename(path), content_type=content_type, size=size, path=path, url=url)
        except Exception as e:
            logger.error(f"Failed to get file info: {path}", exc_info=e)
            return None


class StorageManager:
    """文件存储管理器"""

    def __init__(self):
        self._backend: Optional[StorageBackend] = None
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        """初始化存储管理器"""
        if self._backend:
            return

        async with self._lock:
            if self._backend:
                return

            # 根据配置创建存储后端
            storage_type = config_manager.storage.TYPE
            if storage_type == "local":
                self._backend = LocalStorageBackend(
                    config_manager.storage.LOCAL_ROOT_PATH, config_manager.storage.LOCAL_BASE_URL
                )
            else:
                raise ValueError(f"Unsupported storage type: {storage_type}")

    async def save_file(
        self,
        file: Union[UploadFile, BinaryIO, bytes],
        path: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> FileInfo:
        """
        保存文件
        :param file: 文件对象
        :param path: 存储路径
        :param content_type: 内容类型
        :param metadata: 元数据
        :return: 文件信息
        """
        if not self._backend:
            raise StorageError("Storage manager not initialized")

        start_time = asyncio.get_event_loop().time()
        try:
            file_info = await self._backend.save(file, path, content_type)
            if metadata:
                file_info.metadata.update(metadata)

            # 更新指标
            duration = asyncio.get_event_loop().time() - start_time
            metrics_collector.observe("storage_save_duration_seconds", duration, {"success": "true"})
            metrics_collector.increment("storage_files_saved_total", 1)

            # 发布文件保存事件
            await event_bus.publish(Event("file_saved", file_info.to_dict()))

            return file_info

        except Exception as e:
            # 更新错误指标
            duration = asyncio.get_event_loop().time() - start_time
            metrics_collector.observe("storage_save_duration_seconds", duration, {"success": "false"})
            metrics_collector.increment("storage_save_errors_total", 1)
            raise

    async def save_image(
        self,
        image: Union[UploadFile, BinaryIO, bytes],
        path: str,
        max_size: Optional[tuple] = None,
        format: Optional[str] = None,
        quality: int = 85,
        metadata: Optional[dict] = None,
    ) -> FileInfo:
        """
        保存图片（带优化）
        :param image: 图片对象
        :param path: 存储路径
        :param max_size: 最大尺寸(width, height)
        :param format: 输出格式
        :param quality: 压缩质量
        :param metadata: 元数据
        :return: 文件信息
        """
        if isinstance(image, UploadFile):
            content = await image.read()
        elif isinstance(image, bytes):
            content = image
        else:
            content = image.read()

        # 打开图片
        img = Image.open(content)

        # 调整大小
        if max_size:
            img.thumbnail(max_size)

        # 转换格式
        if format:
            img = img.convert("RGB")

        # 保存图片
        output = img.tobytes()
        content_type = f"image/{format or img.format.lower()}"

        return await self.save_file(output, path, content_type=content_type, metadata=metadata)

    async def delete_file(self, path: str) -> bool:
        """
        删除文件
        :param path: 文件路径
        :return: 是否成功
        """
        if not self._backend:
            raise StorageError("Storage manager not initialized")

        success = await self._backend.delete(path)

        if success:
            # 发布文件删除事件
            await event_bus.publish(Event("file_deleted", {"path": path}))

            metrics_collector.increment("storage_files_deleted_total", 1)

        return success

    async def get_file_url(self, path: str) -> str:
        """
        获取文件URL
        :param path: 文件路径
        :return: 文件URL
        """
        if not self._backend:
            raise StorageError("Storage manager not initialized")

        return await self._backend.get_url(path)

    async def get_file_info(self, path: str) -> Optional[FileInfo]:
        """
        获取文件信息
        :param path: 文件路径
        :return: 文件信息
        """
        if not self._backend:
            raise StorageError("Storage manager not initialized")

        return await self._backend.get_info(path)

    async def exists(self, path: str) -> bool:
        """
        检查文件是否存在
        :param path: 文件路径
        :return: 是否存在
        """
        if not self._backend:
            raise StorageError("Storage manager not initialized")

        return await self._backend.exists(path)

    def generate_path(self, filename: str, category: Optional[str] = None, use_date: bool = True) -> str:
        """
        生成存储路径
        :param filename: 文件名
        :param category: 分类目录
        :param use_date: 是否使用日期目录
        :return: 存储路径
        """
        # 生成文件hash
        name, ext = os.path.splitext(filename)
        file_hash = hashlib.md5(name.encode()).hexdigest()[:8]

        # 构建路径
        parts = []
        if category:
            parts.append(category)

        if use_date:
            now = datetime.now()
            parts.extend([str(now.year), f"{now.month:02d}", f"{now.day:02d}"])

        parts.append(f"{file_hash}{ext}")

        return os.path.join(*parts)


# 创建默认存储管理器实例
storage_manager = StorageManager()

# 导出
__all__ = ["storage_manager", "StorageManager", "StorageBackend", "LocalStorageBackend", "FileInfo", "StorageError"]


# -*- coding:utf-8 -*-
"""
@Project ：Speedy
@File    ：__init__.py.py
@Author  ：PySuper
@Date    ：2025-01-04 16:47
@Desc    ：Speedy __init__.py
"""

import hashlib
import mimetypes
import os
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union


class StorageType(str, Enum):
    """存储类型"""

    ALIYUN_OSS = "aliyun_oss"
    TENCENT_COS = "tencent_cos"
    MINIO = "minio"
    CEPH = "ceph"
    LOCAL = "local"


class StorageProvider(ABC):
    """存储服务提供者接口"""

    @abstractmethod
    async def upload_file(
        self,
        file_path: str,
        data: Union[str, bytes, BinaryIO],
        content_type: Optional[str] = None,
        **kwargs,
    ) -> str:
        """上传文件"""
        pass

    @abstractmethod
    async def download_file(self, file_path: str, local_path: Optional[str] = None, **kwargs) -> Union[bytes, str]:
        """下载文件"""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str, **kwargs) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def get_file_url(self, file_path: str, expires: Optional[int] = None, **kwargs) -> str:
        """获取文件URL"""
        pass

    @abstractmethod
    async def get_file_info(self, file_path: str, **kwargs) -> dict:
        """获取文件信息"""
        pass

    @abstractmethod
    async def list_files(self, prefix: Optional[str] = None, limit: Optional[int] = None, **kwargs) -> list:
        """列出文件"""
        pass

    @abstractmethod
    async def exists(self, file_path: str, **kwargs) -> bool:
        """检查文件是否存在"""
        pass

    async def upload_directory(
        self, local_dir: str, remote_prefix: str = "", exclude_patterns: Optional[List[str]] = None, **kwargs
    ) -> List[str]:
        """上传整个目录"""
        uploaded_files = []
        local_dir_path = Path(local_dir)

        if not local_dir_path.exists() or not local_dir_path.is_dir():
            raise ValueError(f"Directory not found: {local_dir}")

        for root, _, files in os.walk(local_dir):
            for file in files:
                # 检查是否需要排除
                if exclude_patterns:
                    skip = False
                    for pattern in exclude_patterns:
                        if Path(file).match(pattern):
                            skip = True
                            break
                    if skip:
                        continue

                local_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_file_path, local_dir)
                remote_path = os.path.join(remote_prefix, relative_path).replace("\\", "/")

                with open(local_file_path, "rb") as f:
                    content_type = mimetypes.guess_type(file)[0]
                    url = await self.upload_file(remote_path, f, content_type=content_type)
                    uploaded_files.append(url)

        return uploaded_files

    async def download_directory(
        self, remote_prefix: str, local_dir: str, exclude_patterns: Optional[List[str]] = None, **kwargs
    ) -> List[str]:
        """下载整个目录"""
        downloaded_files = []
        local_dir_path = Path(local_dir)
        local_dir_path.mkdir(parents=True, exist_ok=True)

        files = await self.list_files(prefix=remote_prefix)
        for file_info in files:
            file_path = file_info.get("name") or file_info.get("key")

            # 检查是否需要排除
            if exclude_patterns:
                skip = False
                for pattern in exclude_patterns:
                    if Path(file_path).match(pattern):
                        skip = True
                        break
                if skip:
                    continue

            relative_path = os.path.relpath(file_path, remote_prefix)
            local_file_path = os.path.join(local_dir, relative_path)

            # 创建本地目录
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # 下载文件
            await self.download_file(file_path, local_file_path)
            downloaded_files.append(local_file_path)

        return downloaded_files

    async def copy_file(self, source_path: str, target_path: str, **kwargs) -> str:
        """复制文件"""
        content = await self.download_file(source_path)
        if isinstance(content, str):
            content = content.encode()
        return await self.upload_file(target_path, content)

    async def move_file(self, source_path: str, target_path: str, **kwargs) -> str:
        """移动文件"""
        url = await self.copy_file(source_path, target_path)
        await self.delete_file(source_path)
        return url

    async def calculate_file_hash(self, file_path: str, hash_type: str = "md5", **kwargs) -> str:
        """计算文件哈希值"""
        content = await self.download_file(file_path)
        if isinstance(content, str):
            content = content.encode()

        hash_obj = hashlib.new(hash_type)
        hash_obj.update(content)
        return hash_obj.hexdigest()

    async def get_file_size(self, file_path: str, **kwargs) -> int:
        """获取文件大小"""
        info = await self.get_file_info(file_path)
        return info.get("size") or info.get("content_length", 0)

    async def batch_delete(self, file_paths: List[str], **kwargs) -> Dict[str, bool]:
        """批量删除文件"""
        results = {}
        for file_path in file_paths:
            try:
                success = await self.delete_file(file_path)
                results[file_path] = success
            except Exception as e:
                results[file_path] = False
        return results

    async def batch_exists(self, file_paths: List[str], **kwargs) -> Dict[str, bool]:
        """批量检查文件是否存在"""
        results = {}
        for file_path in file_paths:
            try:
                exists = await self.exists(file_path)
                results[file_path] = exists
            except Exception as e:
                results[file_path] = False
        return results
