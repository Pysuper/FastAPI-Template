"""
使用队列来异步写入日志
使用缓冲区来批量写入
使用专门的日志服务器
"""

import time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from core.config.load.base import BaseConfig


class LogLevel(str, Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """日志格式"""

    # TEXT = "text"
    TEXT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    JSON = "json"


class LogConfig(BaseModel):
    """日志配置"""

    # 最新配置
    ROTATION: bool = True
    FILE_SIZE: int = 10 * 1024 * 1024

    # 基本配置
    LOG_DIR: str = "logs"
    LEVEL: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    FORMAT: LogFormat = Field(default=LogFormat.TEXT, description="日志格式")
    DATE_FORMAT: str = Field(default="%Y-%m-%d %H:%M:%S", description="日期格式")
    BASE_LOG_FORMAT: str = Field(default="%(asctime)s [%(levelname)s] %(message)s", description="基础日志格式")

    # 文件配置
    FILE_PATH: str = Field(default="logs/app.log", description="日志文件路径")
    MAX_BYTES: int = Field(default=10 * 1024 * 1024, description="单个日志文件最大大小")
    BACKUP_COUNT: int = Field(default=5, description="保留的日志文件数量")
    ENCODING: str = Field(default="utf-8", description="日志文件编码")

    # 控制台配置
    CONSOLE_ENABLED: bool = Field(default=True, description="是否启用控制台日志")
    CONSOLE_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="控制台日志级别")

    # 文件输出配置
    FILE_ENABLED: bool = Field(default=True, description="是否启用文件日志")
    FILE_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="文件日志级别")

    # 日志轮转配置
    # ROTATION: str = Field(default="500MB", description="日志轮转大小")
    RETENTION: str = Field(default="10 days", description="日志保留时间")
    COMPRESSION: str = Field(default="zip", description="日志压缩格式")

    # JSON格式配置
    JSON_ENSURE_ASCII: bool = Field(default=False, description="JSON是否确保ASCII")
    JSON_INDENT: Optional[int] = Field(default=None, description="JSON缩进")
    JSON_SORT_KEYS: bool = Field(default=False, description="JSON是否排序键")
    LOG_CONSOLE_OUTPUT: bool = Field(default=False, description="是否输出到控制台")
    LOG_FILE_OUTPUT: bool = Field(default=True, description="是否输出到文件")
    LOG_JSON_OUTPUT: bool = Field(default=True, description="是否输出到JSON")
    LOG_JSON_FORMAT: bool = Field(default=True, description="是否格式化JSON")
    LOG_ERROR_FILE_OUTPUT: bool = Field(default=True, description="是否输出错误日志到文件")

    # 其他配置
    PROPAGATE: bool = Field(default=False, description="是否传播日志到父级")
    INCLUDE_TIMESTAMP: bool = Field(default=True, description="是否包含时间戳")
    INCLUDE_HOSTNAME: bool = Field(default=True, description="是否包含主机名")
    INCLUDE_PROCESS: bool = Field(default=True, description="是否包含进程信息")

    # 增加配置
    CONSOLE_OUTPUT: bool = Field(default=True, description="是否输出到控制台")
    FILE_OUTPUT: bool = Field(default=True, description="是否输出到文件")
    JSON_OUTPUT: bool = Field(default=True, description="是否输出到JSON")
    JSON_FORMAT: bool = Field(default=True, description="是否格式化JSON")
    ERROR_FILE_OUTPUT: bool = Field(default=True, description="是否输出错误日志到文件")

    class Config:
        env_prefix = "LOG_"
        use_enum_values = True


class LoggingConfig(BaseConfig):
    """日志配置类"""

    model_config = ConfigDict(
        title="日志配置",
        json_schema_extra={
            "description": "日志配置，包括日志级别、目录、轮转、告警等设置",
        },
    )

    # 基本配置
    log_level: str = "INFO"
    log_dir: str = "logs"
    file_logging: bool = True
    console_logging: bool = True

    # 异步日志
    async_logging: bool = True
    queue_size: int = 1000

    # 日志轮转
    rotation_max_bytes: int = 10485760  # 10MB
    rotation_backup_count: int = 30
    rotation_compress: bool = True

    # 日志告警
    alert_enabled: bool = True
    alert_error_threshold: int = 10
    alert_interval: int = 3600  # 1小时
    alert_channels: List[str] = ["email"]
    alert_receivers: List[str] = ["admin@example.com"]

    def __init__(self, **data):
        super().__init__(**data)
        self._setup_logging()

    def _setup_logging(self):
        """设置日志系统"""
        import logging
        import logging.handlers
        import os
        import queue
        import threading
        from concurrent.futures import ThreadPoolExecutor

        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)

        # 创建根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))

        # 清除现有的处理器
        root_logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        if self.console_logging:
            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        if self.file_logging:
            # 添加文件处理器（带轮转）
            log_file = os.path.join(self.log_dir, "app.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=self.rotation_max_bytes, backupCount=self.rotation_backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            # 如果启用了压缩，添加轮转后的处理器
            if self.rotation_compress:

                def compress_log(source_path):
                    import gzip
                    import shutil

                    with open(source_path, "rb") as f_in:
                        with gzip.open(f"{source_path}.gz", "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(source_path)

                def rotate_callback(source_path):
                    threading.Thread(target=compress_log, args=(source_path,)).start()

                file_handler.rotator = rotate_callback

        if self.async_logging:
            # 设置异步日志
            log_queue = queue.Queue(maxsize=self.queue_size)
            queue_handler = logging.handlers.QueueHandler(log_queue)
            root_logger.addHandler(queue_handler)

            # 创建队列监听器
            queue_listener = logging.handlers.QueueListener(
                log_queue, *root_logger.handlers[:-1], respect_handler_level=True  # 除了QueueHandler之外的所有处理器
            )
            queue_listener.start()

        if self.alert_enabled:
            # 添加告警处理器
            class AlertHandler(logging.Handler):
                def __init__(self, config: "LoggingConfig"):
                    super().__init__()
                    self.config = config
                    self.error_count = 0
                    self.last_alert_time = 0
                    self.lock = threading.Lock()
                    self.executor = ThreadPoolExecutor(max_workers=1)

                def emit(self, record):
                    if record.levelno >= logging.ERROR:
                        with self.lock:
                            self.error_count += 1
                            current_time = time.time()
                            if (
                                self.error_count >= self.config.alert_error_threshold
                                and current_time - self.last_alert_time >= self.config.alert_interval
                            ):
                                self.executor.submit(self._send_alert)
                                self.error_count = 0
                                self.last_alert_time = current_time

                def _send_alert(self):
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                    from core.config.settings import ConfigManager

                    config = ConfigManager()
                    if "email" in self.config.alert_channels:
                        msg = MIMEMultipart()
                        msg["Subject"] = f"[ERROR] Log Alert - Error threshold exceeded"
                        msg["From"] = config.email.sender
                        msg["To"] = ", ".join(self.config.alert_receivers)

                        body = f"""
                        Error threshold ({self.config.alert_error_threshold}) has been exceeded in the last {self.config.alert_interval} seconds.
                        Please check the logs for more details.
                        """
                        msg.attach(MIMEText(body, "plain"))

                        try:
                            with smtplib.SMTP(config.email.smtp_server, config.email.smtp_port) as server:
                                if config.email.use_tls:
                                    server.starttls()
                                server.login(config.email.username, config.email.password)
                                server.send_message(msg)
                        except Exception as e:
                            logging.error(f"Failed to send alert email: {e}")

            alert_handler = AlertHandler(self)
            alert_handler.setLevel(logging.ERROR)
            root_logger.addHandler(alert_handler)
