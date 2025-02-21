import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiofiles
import aiofiles.os
from PIL import Image
from fastapi import UploadFile

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger

logger = get_logger("file_utils")


class FileManager:
    """文件管理器"""

    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, filename: str, sub_dir: Optional[str] = None) -> Path:
        """获取文件路径"""
        if sub_dir:
            path = self.base_path / sub_dir
            path.mkdir(parents=True, exist_ok=True)
            return path / filename
        return self.base_path / filename

    def _get_file_hash(self, content: bytes) -> str:
        """计算文件哈希值"""
        return hashlib.md5(content).hexdigest()

    async def save_file(
        self,
        file: UploadFile,
        sub_dir: Optional[str] = None,
        max_size: int = 10 * 1024 * 1024,  # 10MB
    ) -> dict:
        """保存文件"""
        try:
            content = await file.read()
            if len(content) > max_size:
                raise ValueError(f"文件大小超过限制: {max_size} bytes")

            # 生成唯一文件名
            file_hash = self._get_file_hash(content)
            ext = Path(file.filename).suffix
            new_filename = f"{file_hash}{ext}"

            # 保存文件
            file_path = self._get_file_path(new_filename, sub_dir)
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            return {
                "filename": new_filename,
                "original_filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "path": str(file_path),
                "hash": file_hash,
            }

        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            raise

    async def save_image(
        self,
        file: UploadFile,
        sub_dir: Optional[str] = None,
        max_size: int = 5 * 1024 * 1024,  # 5MB
        max_dimensions: tuple = (2000, 2000),
        thumbnail_size: tuple = (200, 200),
    ) -> dict:
        """保存图片（包含缩略图生成）"""
        try:
            content = await file.read()
            if len(content) > max_size:
                raise ValueError(f"图片大小超过限制: {max_size} bytes")

            # 验证和处理图片
            img = Image.open(file.file)
            if img.size[0] > max_dimensions[0] or img.size[1] > max_dimensions[1]:
                img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

            # 生成唯一文件名
            file_hash = self._get_file_hash(content)
            ext = Path(file.filename).suffix.lower()
            if ext not in [".jpg", ".jpeg", ".png", ".gif"]:
                raise ValueError("不支持的图片格式")

            new_filename = f"{file_hash}{ext}"
            thumb_filename = f"{file_hash}_thumb{ext}"

            # 保存原图
            file_path = self._get_file_path(new_filename, sub_dir)
            img.save(file_path, quality=85, optimize=True)

            # 生成并保存缩略图
            thumb = img.copy()
            thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            thumb_path = self._get_file_path(thumb_filename, sub_dir)
            thumb.save(thumb_path, quality=85, optimize=True)

            return {
                "filename": new_filename,
                "thumbnail": thumb_filename,
                "original_filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "dimensions": img.size,
                "path": str(file_path),
                "thumbnail_path": str(thumb_path),
                "hash": file_hash,
            }

        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            raise
        finally:
            if file.file:
                file.file.close()

    async def delete_file(self, filename: str, sub_dir: Optional[str] = None) -> bool:
        """删除文件"""
        try:
            file_path = self._get_file_path(filename, sub_dir)
            if await aiofiles.os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            raise

    async def get_file_info(self, filename: str, sub_dir: Optional[str] = None) -> Optional[dict]:
        """获取文件信息"""
        try:
            file_path = self._get_file_path(filename, sub_dir)
            if not await aiofiles.os.path.exists(file_path):
                return None

            stats = await aiofiles.os.stat(file_path)
            return {
                "filename": filename,
                "path": str(file_path),
                "size": stats.st_size,
                "created_at": datetime.fromtimestamp(stats.st_ctime),
                "modified_at": datetime.fromtimestamp(stats.st_mtime),
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            raise

    async def list_files(self, sub_dir: Optional[str] = None) -> List[dict]:
        """列出目录下的所有文件"""
        try:
            path = self.base_path
            if sub_dir:
                path = path / sub_dir

            if not await aiofiles.os.path.exists(path):
                return []

            files = []
            async for entry in aiofiles.os.scandir(path):
                if entry.is_file():
                    stats = await aiofiles.os.stat(entry.path)
                    files.append(
                        {
                            "filename": entry.name,
                            "path": str(entry.path),
                            "size": stats.st_size,
                            "created_at": datetime.fromtimestamp(stats.st_ctime),
                            "modified_at": datetime.fromtimestamp(stats.st_mtime),
                        }
                    )
            return files
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise


# 创建全局文件管理器实例
file_manager = FileManager(settings.UPLOAD_DIR)
