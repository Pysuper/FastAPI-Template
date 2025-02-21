import asyncio
import logging
from asyncio import Queue
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """日志条目"""

    log_type: str  # 日志类型
    content: Dict  # 日志内容
    timestamp: datetime = None  # 时间戳

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AsyncLogWriter:
    """异步日志写入器"""

    def __init__(
        self,
        log_dir: str,
        max_queue_size: int = 10000,  # 最大队列大小
        batch_size: int = 100,  # 批量写入大小
        flush_interval: float = 1.0,  # 刷新间隔(秒)
        max_file_size: int = 100 * 1024 * 1024,  # 最大文件大小(100MB)
        max_files: int = 10,  # 最大文件数
    ):
        self.log_dir = Path(log_dir)
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_file_size = max_file_size
        self.max_files = max_files

        self.queue: Queue[LogEntry] = Queue(maxsize=max_queue_size)
        self.current_file: Dict[str, Path] = {}  # log_type -> current_file
        self.current_size: Dict[str, int] = {}  # log_type -> current_size
        self._worker_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # 统计信息
        self._stats = {
            "total_entries": 0,
            "dropped_entries": 0,
            "batch_writes": 0,
            "total_bytes": 0,
            "queue_full_count": 0,
        }

        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self, log_type: str) -> Path:
        """获取日志文件"""
        if log_type not in self.current_file or self.current_size[log_type] >= self.max_file_size:
            self._rotate_files(log_type)

        return self.current_file[log_type]

    def _rotate_files(self, log_type: str):
        """轮转日志文件"""
        # 获取该类型的所有日志文件
        log_files = sorted(self.log_dir.glob(f"{log_type}_*.log"), key=lambda p: p.stat().st_mtime)

        # 如果文件数超过限制,删除最旧的文件
        while len(log_files) >= self.max_files:
            log_files[0].unlink()
            log_files = log_files[1:]

        # 创建新文件
        new_file = self.log_dir / f"{log_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.current_file[log_type] = new_file
        self.current_size[log_type] = 0

    async def write(self, entry: LogEntry):
        """写入日志条目"""
        try:
            await self.queue.put(entry)
        except asyncio.QueueFull:
            self._stats["dropped_entries"] += 1
            self._stats["queue_full_count"] += 1
            logger.warning("Log queue is full, dropping entry")

    async def _write_batch(self, entries: List[LogEntry]):
        """批量写入日志"""
        # 按日志类型分组
        entries_by_type: Dict[str, List[LogEntry]] = {}
        for entry in entries:
            if entry.log_type not in entries_by_type:
                entries_by_type[entry.log_type] = []
            entries_by_type[entry.log_type].append(entry)

        # 写入每种类型的日志
        for log_type, type_entries in entries_by_type.items():
            log_file = self._get_log_file(log_type)

            # 写入日志
            content = "\n".join(f"{entry.timestamp.isoformat()} {str(entry.content)}" for entry in type_entries) + "\n"

            content_size = len(content.encode("utf-8"))

            # 如果写入后会超过文件大小限制,先轮转文件
            if self.current_size[log_type] + content_size > self.max_file_size:
                self._rotate_files(log_type)
                log_file = self.current_file[log_type]

            # 写入文件
            with log_file.open("a", encoding="utf-8") as f:
                f.write(content)

            # 更新文件大小
            self.current_size[log_type] += content_size

            # 更新统计信息
            self._stats["total_entries"] += len(type_entries)
            self._stats["total_bytes"] += content_size

    async def _worker(self):
        """日志写入工作器"""
        batch: List[LogEntry] = []
        last_flush = asyncio.get_event_loop().time()

        while not self._stop_event.is_set():
            try:
                # 等待新的日志条目或刷新间隔
                try:
                    entry = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=max(0, self.flush_interval - (asyncio.get_event_loop().time() - last_flush)),
                    )
                    batch.append(entry)
                except asyncio.TimeoutError:
                    pass

                # 检查是否需要刷新
                now = asyncio.get_event_loop().time()
                should_flush = len(batch) >= self.batch_size or (batch and now - last_flush >= self.flush_interval)

                if should_flush:
                    await self._write_batch(batch)
                    self._stats["batch_writes"] += 1
                    batch = []
                    last_flush = now

            except Exception as e:
                logger.error(f"Error in log writer worker: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """启动日志写入器"""
        if self._worker_task is None:
            self._stop_event.clear()
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("Log writer started")

    async def stop(self):
        """停止日志写入器"""
        if self._worker_task:
            self._stop_event.set()

            # 等待队列中的日志写入完成
            if not self.queue.empty():
                try:
                    remaining = []
                    while not self.queue.empty():
                        remaining.append(await self.queue.get())
                    if remaining:
                        await self._write_batch(remaining)
                except Exception as e:
                    logger.error(f"Error writing remaining logs: {e}")

            await self._worker_task
            self._worker_task = None
            logger.info("Log writer stopped")

    def get_metrics(self) -> Dict:
        """获取写入器指标"""
        return {
            "config": {
                "max_queue_size": self.max_queue_size,
                "batch_size": self.batch_size,
                "flush_interval": self.flush_interval,
                "max_file_size": self.max_file_size,
                "max_files": self.max_files,
            },
            "current_state": {
                "queue_size": self.queue.qsize(),
                "is_running": self._worker_task is not None,
            },
            "stats": self._stats.copy(),
        }
