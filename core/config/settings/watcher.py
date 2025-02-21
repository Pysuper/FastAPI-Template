import logging
from typing import Any, Callable, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器"""

    def __init__(self, callback: Callable):
        """
        初始化
        :param callback: 配置变更回调函数
        """
        self.callback = callback

    def on_modified(self, event: FileSystemEvent) -> None:
        """
        文件修改事件处理
        :param event: 文件系统事件
        """
        if event.is_directory:
            return

        logger.info(f"配置文件已修改: {event.src_path}")
        self.callback()


class ConfigWatcher:
    """
    配置监控器
    """

    def __init__(self):
        self._observer: Optional[Observer] = None
        self._handler: Optional[ConfigFileHandler] = None
        self._watching = False

    def start(self, config_dir: str, callback: Callable) -> None:
        """
        启动监控
        :param config_dir: 配置目录
        :param callback: 配置变更回调函数
        """
        if self._watching:
            return

        # 创建事件处理器
        self._handler = ConfigFileHandler(callback)

        # 创建观察者
        self._observer = Observer()
        self._observer.schedule(self._handler, config_dir, recursive=False)

        # 启动观察者
        self._observer.start()
        self._watching = True

        logger.info(f"开始监控配置目录: {config_dir}")

    def stop(self) -> None:
        """停止监控"""
        if not self._watching:
            return

        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        self._handler = None
        self._watching = False

        logger.info("停止监控配置目录")

    @property
    def is_watching(self) -> bool:
        """是否正在监控"""
        return self._watching

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


class ConfigChangeEvent:
    """
    配置变更事件
    """

    def __init__(self, config_name: str, old_value: Any, new_value: Any):
        self.config_name = config_name
        self.old_value = old_value
        self.new_value = new_value


class ConfigChangeListener:
    """
    配置变更监听器
    """

    def on_config_change(self, event: ConfigChangeEvent) -> None:
        pass


# 创建全局配置监控器实例
config_watcher = ConfigWatcher()
