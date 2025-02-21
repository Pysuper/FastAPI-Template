import os
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path

import aioboto3
from croniter import croniter

from core.config.setting import settings
from core.loge.pysuper_logging import get_logger

logger = get_logger("backup")


class BackupManager:
    """备份管理器"""

    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # S3会话
        if settings.DR_ENABLED:
            self.s3_session = aioboto3.Session()

    def _get_backup_name(self) -> str:
        """生成备份文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}.tar.gz"

    async def create_backup(self) -> dict:
        """创建备份"""
        try:
            backup_name = self._get_backup_name()
            backup_path = self.backup_dir / backup_name

            # 创建临时目录
            temp_dir = self.backup_dir / "temp"
            temp_dir.mkdir(exist_ok=True)

            try:
                # 备份数据库
                await self._backup_database(temp_dir)

                # 备份上传的文件
                await self._backup_uploads(temp_dir)

                # 备份配置文件
                await self._backup_configs(temp_dir)

                # 创建压缩文件
                with tarfile.open(backup_path, "w:gz") as tar:
                    tar.add(temp_dir, arcname="")

                # 获取备份文件大小
                size = os.path.getsize(backup_path)

                # 检查备份大小
                if size > settings.BACKUP_MAX_SIZE:
                    raise ValueError(f"Backup size exceeds limit: {size} bytes")

                # 如果启用了灾难恢复，上传到S3
                if settings.DR_ENABLED:
                    await self._upload_to_s3(backup_path)

                return {
                    "name": backup_name,
                    "path": str(backup_path),
                    "size": size,
                    "timestamp": datetime.now().isoformat(),
                }

            finally:
                # 清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            raise

    async def _backup_database(self, temp_dir: Path):
        """备份数据库"""
        try:
            # 使用mysqldump命令备份数据库
            dump_file = temp_dir / "database.sql"
            cmd = (
                f"mysqldump -h {settings.MYSQL_SERVER} "
                f"-P {settings.MYSQL_PORT} "
                f"-u {settings.MYSQL_USER} "
                f"-p{settings.MYSQL_PASSWORD} "
                f"{settings.MYSQL_DB} > {dump_file}"
            )
            os.system(cmd)
        except Exception as e:
            logger.error(f"Failed to backup database: {str(e)}")
            raise

    async def _backup_uploads(self, temp_dir: Path):
        """备份上传的文件"""
        try:
            upload_dir = Path(settings.UPLOAD_DIR)
            if upload_dir.exists():
                shutil.copytree(upload_dir, temp_dir / "uploads", dirs_exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to backup uploads: {str(e)}")
            raise

    async def _backup_configs(self, temp_dir: Path):
        """备份配置文���"""
        try:
            # 备份.env文件
            env_file = Path(".env")
            if env_file.exists():
                shutil.copy2(env_file, temp_dir / ".env")

            # 备份其他配置文件
            config_dir = Path("config")
            if config_dir.exists():
                shutil.copytree(config_dir, temp_dir / "config", dirs_exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to backup configs: {str(e)}")
            raise

    async def _upload_to_s3(self, backup_path: Path):
        """上传备份到S3"""
        try:
            bucket = settings.DR_BACKUP_LOCATION.split("://")[1]
            key = f"backups/{backup_path.name}"

            async with self.s3_session.client("s3") as s3:
                with open(backup_path, "rb") as f:
                    await s3.upload_fileobj(f, bucket, key)

            logger.info(f"Backup uploaded to S3: {key}")
        except Exception as e:
            logger.error(f"Failed to upload backup to S3: {str(e)}")
            raise

    async def restore_backup(self, backup_name: str) -> bool:
        """恢复备份"""
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_name}")

            # 创建临时目录
            temp_dir = self.backup_dir / "temp_restore"
            temp_dir.mkdir(exist_ok=True)

            try:
                # 解压备份文件
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(temp_dir)

                # 恢复数据库
                await self._restore_database(temp_dir)

                # 恢复上传的文件
                await self._restore_uploads(temp_dir)

                # 恢复配置文件
                await self._restore_configs(temp_dir)

                return True

            finally:
                # 清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

        except Exception as e:
            logger.error(f"Failed to restore backup: {str(e)}")
            raise

    async def _restore_database(self, temp_dir: Path):
        """恢复数据库"""
        try:
            dump_file = temp_dir / "database.sql"
            if dump_file.exists():
                cmd = (
                    f"mysql -h {settings.MYSQL_SERVER} "
                    f"-P {settings.MYSQL_PORT} "
                    f"-u {settings.MYSQL_USER} "
                    f"-p{settings.MYSQL_PASSWORD} "
                    f"{settings.MYSQL_DB} < {dump_file}"
                )
                os.system(cmd)
        except Exception as e:
            logger.error(f"Failed to restore database: {str(e)}")
            raise

    async def _restore_uploads(self, temp_dir: Path):
        """恢复上传的文件"""
        try:
            upload_source = temp_dir / "uploads"
            if upload_source.exists():
                upload_dir = Path(settings.UPLOAD_DIR)
                if upload_dir.exists():
                    shutil.rmtree(upload_dir)
                shutil.copytree(upload_source, upload_dir)
        except Exception as e:
            logger.error(f"Failed to restore uploads: {str(e)}")
            raise

    async def _restore_configs(self, temp_dir: Path):
        """恢复配置文件"""
        try:
            # 恢复.env文件
            env_file = temp_dir / ".env"
            if env_file.exists():
                shutil.copy2(env_file, ".env")

            # 恢复其他配置文件
            config_source = temp_dir / "config"
            if config_source.exists():
                config_dir = Path("config")
                if config_dir.exists():
                    shutil.rmtree(config_dir)
                shutil.copytree(config_source, config_dir)
        except Exception as e:
            logger.error(f"Failed to restore configs: {str(e)}")
            raise

    async def cleanup_old_backups(self):
        """清理旧备份"""
        try:
            retention_days = settings.BACKUP_RETENTION_DAYS
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            # 清理本地备份
            for backup_file in self.backup_dir.glob("backup_*.tar.gz"):
                try:
                    # 从文件名中提取时间戳
                    timestamp_str = backup_file.stem.split("_")[1]
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if timestamp < cutoff_date:
                        backup_file.unlink()
                        logger.info(f"Deleted old backup: {backup_file.name}")
                except Exception as e:
                    logger.error(f"Failed to process backup file {backup_file}: {str(e)}")

            # 清理S3备份
            if settings.DR_ENABLED:
                await self._cleanup_s3_backups(cutoff_date)

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
            raise

    async def _cleanup_s3_backups(self, cutoff_date: datetime):
        """清理S3上的旧备份"""
        try:
            bucket = settings.DR_BACKUP_LOCATION.split("://")[1]

            async with self.s3_session.client("s3") as s3:
                paginator = s3.get_paginator("list_objects_v2")

                async for page in paginator.paginate(Bucket=bucket, Prefix="backups/backup_"):
                    if "Contents" not in page:
                        continue

                    for obj in page["Contents"]:
                        try:
                            # 从文件名中提取时间戳
                            key = obj["Key"]
                            filename = key.split("/")[-1]
                            timestamp_str = filename.split("_")[1].split(".")[0]
                            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                            if timestamp < cutoff_date:
                                await s3.delete_object(Bucket=bucket, Key=key)
                                logger.info(f"Deleted old S3 backup: {key}")
                        except Exception as e:
                            logger.error(f"Failed to process S3 object {key}: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to cleanup S3 backups: {str(e)}")
            raise

    async def should_run_backup(self) -> bool:
        """检查是否应该运行备份"""
        try:
            cron = croniter(settings.BACKUP_SCHEDULE)
            next_run = cron.get_prev(datetime)
            now = datetime.now()

            # 如果距离上次计划运行时间在5分钟内，则运行备份
            return abs((now - next_run).total_seconds()) <= 300

        except Exception as e:
            logger.error(f"Failed to check backup schedule: {str(e)}")
            return False


# 创建全局备份管理器实例
backup_manager = BackupManager()
