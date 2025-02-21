import os
from pathlib import Path
from typing import Optional

from dotenv import find_dotenv, load_dotenv


class EnvManager:
    """环境变量管理器"""

    def __init__(self):
        self._env_file: Optional[str] = None
        self._env_loaded: bool = False
        # 假设通过环境变量来判断是否为生产环境
        self.is_prod = os.getenv("PRODUCTION", False) == "True"
        self.is_dev = not self.is_prod
        # 设置环境变量文件的根目录
        self.env_dir = Path(".env")

    def get_env_file(self) -> str:
        """获取环境变量文件路径"""
        if not self._env_file:
            # 首先检查是否有环境变量指定的配置文件
            env_file = os.getenv("ENV_FILE")

            if not env_file:
                # 根据环境变量 APP_ENV 选择配置文件
                app_env = os.getenv("APP_ENV", "dev").lower()
                env_file = self.env_dir / f".env.{app_env}"

                # 如果指定环境的配置文件不存在，使用默认的 .env 文件
                if not env_file.exists():
                    env_file = self.env_dir / ".env"

            # 使用 python-dotenv 的 find_dotenv 函数查找配置文件
            self._env_file = find_dotenv(env_file, usecwd=True)

            if not self._env_file:
                raise FileNotFoundError(f"找不到环境变量配置文件: {env_file}")

        return self._env_file

    def setup_environment(self) -> None:
        """设置环境变量"""
        if not self._env_loaded:
            env_file = self.get_env_file()
            load_dotenv(env_file)
            self._env_loaded = True

            # 设置一些基本的环境变量
            os.environ.setdefault("PYTHONPATH", "")
            os.environ.setdefault("PYTHONUNBUFFERED", "1")

            # 创建必要的目录
            self._create_directories()

            # 打印环境信息（仅在开发环境）
            if os.getenv("APP_ENV", "dev").lower() == "dev":
                print(f"已加载环境变量配置文件: {env_file}")

    def _create_directories(self) -> None:
        """创建必要的目录"""
        directories = [
            "logs",  # 日志目录
            "uploads",  # 上传文件目录
            "temp",  # 临时文件目录
            os.getenv("UPLOAD_DIR", "uploads"),  # 配置的上传目录
            os.getenv("BACKUP_DIR", "backups"),  # 配置的备份目录
        ]

        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)

    def reload(self) -> None:
        """重新加载环境变量"""
        self._env_loaded = False
        self._env_file = None
        self.setup_environment()


# 创建全局环境变量管理器实例
env_manager = EnvManager()
