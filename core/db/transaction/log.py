import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from .distributed import DistributedTransaction

logger = logging.getLogger(__name__)


class LogEntryType(Enum):
    """日志条目类型"""

    TRANSACTION_START = "transaction_start"
    TRANSACTION_PREPARE = "transaction_prepare"
    TRANSACTION_COMMIT = "transaction_commit"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    TRANSACTION_COMPLETE = "transaction_complete"
    PARTICIPANT_PREPARE = "participant_prepare"
    PARTICIPANT_COMMIT = "participant_commit"
    PARTICIPANT_ROLLBACK = "participant_rollback"
    ERROR = "error"


class TransactionLogEntry:
    """事务日志条目"""

    def __init__(
        self,
        transaction_id: str,
        entry_type: LogEntryType,
        timestamp: datetime = None,
        participant_name: str = None,
        state: str = None,
        error: str = None,
        details: Dict = None,
    ):
        self.transaction_id = transaction_id
        self.entry_type = entry_type
        self.timestamp = timestamp or datetime.now()
        self.participant_name = participant_name
        self.state = state
        self.error = error
        self.details = details or {}

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "transaction_id": self.transaction_id,
            "entry_type": self.entry_type.value,
            "timestamp": self.timestamp.isoformat(),
            "participant_name": self.participant_name,
            "state": self.state,
            "error": self.error,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TransactionLogEntry":
        """从字典创建日志条目"""
        return cls(
            transaction_id=data["transaction_id"],
            entry_type=LogEntryType(data["entry_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            participant_name=data.get("participant_name"),
            state=data.get("state"),
            error=data.get("error"),
            details=data.get("details", {}),
        )


class TransactionLog:
    """事务日志"""

    def __init__(
        self,
        log_dir: str = "logs/transactions",
        max_file_size: int = 10 * 1024 * 1024,
        max_files: int = 10,  # 10MB
    ):
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.current_file: Optional[Path] = None
        self.current_size = 0

        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 初始化当前日志文件
        self._init_current_file()

    def _init_current_file(self):
        """初始化当前日志文件"""
        # 查找最新的日志文件
        log_files = sorted(self.log_dir.glob("transaction_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)

        if not log_files:
            # 创建新文件
            self.current_file = self.log_dir / f"transaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            self.current_size = 0
        else:
            self.current_file = log_files[0]
            self.current_size = self.current_file.stat().st_size

        # 如果当前文件大小超过限制,创建新文件
        if self.current_size >= self.max_file_size:
            self._rotate_files()

    def _rotate_files(self):
        """轮转日志文件"""
        # 获取所有日志文件
        log_files = sorted(self.log_dir.glob("transaction_*.log"), key=lambda p: p.stat().st_mtime)

        # 如果文件数超过限制,删除最旧的文件
        while len(log_files) >= self.max_files:
            log_files[0].unlink()
            log_files = log_files[1:]

        # 创建新文件
        self.current_file = self.log_dir / f"transaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.current_size = 0

    def _write_entry(self, entry: TransactionLogEntry):
        """写入日志条目"""
        # 如果当前文件大小超过限制,轮转文件
        if self.current_size >= self.max_file_size:
            self._rotate_files()

        # 写入日志条目
        entry_data = json.dumps(entry.to_dict()) + "\n"
        entry_size = len(entry_data.encode("utf-8"))

        with self.current_file.open("a", encoding="utf-8") as f:
            f.write(entry_data)

        self.current_size += entry_size

    def log_transaction_start(self, transaction: DistributedTransaction):
        """记录事务开始"""
        entry = TransactionLogEntry(
            transaction_id=transaction.transaction_id,
            entry_type=LogEntryType.TRANSACTION_START,
            state=transaction.state.value,
            details={
                "coordinator_timeout": transaction.coordinator_timeout,
                "participant_timeout": transaction.participant_timeout,
            },
        )
        self._write_entry(entry)

    def log_transaction_prepare(self, transaction: DistributedTransaction):
        """记录事务准备阶段"""
        entry = TransactionLogEntry(
            transaction_id=transaction.transaction_id,
            entry_type=LogEntryType.TRANSACTION_PREPARE,
            state=transaction.state.value,
            details={"participants": [p.name for p in transaction.participants]},
        )
        self._write_entry(entry)

    def log_transaction_commit(self, transaction: DistributedTransaction):
        """记录事务提交阶段"""
        entry = TransactionLogEntry(
            transaction_id=transaction.transaction_id,
            entry_type=LogEntryType.TRANSACTION_COMMIT,
            state=transaction.state.value,
        )
        self._write_entry(entry)

    def log_transaction_rollback(self, transaction: DistributedTransaction):
        """记录事务回滚阶段"""
        entry = TransactionLogEntry(
            transaction_id=transaction.transaction_id,
            entry_type=LogEntryType.TRANSACTION_ROLLBACK,
            state=transaction.state.value,
            error=str(transaction.error) if transaction.error else None,
        )
        self._write_entry(entry)

    def log_transaction_complete(self, transaction: DistributedTransaction):
        """记录事务完成"""
        entry = TransactionLogEntry(
            transaction_id=transaction.transaction_id,
            entry_type=LogEntryType.TRANSACTION_COMPLETE,
            state=transaction.state.value,
            details={
                "started_at": transaction.started_at.isoformat(),
                "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
                "duration": (transaction.completed_at - transaction.started_at).total_seconds()
                if transaction.completed_at
                else None,
            },
        )
        self._write_entry(entry)

    def log_participant_prepare(self, transaction_id: str, participant_name: str, success: bool, error: str = None):
        """记录参与者准备阶段"""
        entry = TransactionLogEntry(
            transaction_id=transaction_id,
            entry_type=LogEntryType.PARTICIPANT_PREPARE,
            participant_name=participant_name,
            state="prepared" if success else "failed",
            error=error,
        )
        self._write_entry(entry)

    def log_participant_commit(self, transaction_id: str, participant_name: str, success: bool, error: str = None):
        """记录参与者提交阶段"""
        entry = TransactionLogEntry(
            transaction_id=transaction_id,
            entry_type=LogEntryType.PARTICIPANT_COMMIT,
            participant_name=participant_name,
            state="committed" if success else "failed",
            error=error,
        )
        self._write_entry(entry)

    def log_participant_rollback(self, transaction_id: str, participant_name: str, success: bool, error: str = None):
        """记录参与者回滚阶段"""
        entry = TransactionLogEntry(
            transaction_id=transaction_id,
            entry_type=LogEntryType.PARTICIPANT_ROLLBACK,
            participant_name=participant_name,
            state="rolled_back" if success else "failed",
            error=error,
        )
        self._write_entry(entry)

    def log_error(self, transaction_id: str, error: Exception, details: Dict = None):
        """记录错误"""
        entry = TransactionLogEntry(
            transaction_id=transaction_id, entry_type=LogEntryType.ERROR, error=str(error), details=details
        )
        self._write_entry(entry)

    def get_transaction_log(self, transaction_id: str) -> List[TransactionLogEntry]:
        """获取事务日志"""
        entries = []

        # 遍历所有日志文件
        for log_file in sorted(self.log_dir.glob("transaction_*.log"), key=lambda p: p.stat().st_mtime):
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry_data = json.loads(line)
                        if entry_data["transaction_id"] == transaction_id:
                            entries.append(TransactionLogEntry.from_dict(entry_data))
                    except Exception as e:
                        logger.error(f"Failed to parse log entry: {e}")

        return sorted(entries, key=lambda e: e.timestamp)

    def get_metrics(self) -> Dict:
        """获取日志指标"""
        log_files = list(self.log_dir.glob("transaction_*.log"))
        total_size = sum(f.stat().st_size for f in log_files)

        return {
            "log_dir": str(self.log_dir),
            "max_file_size": self.max_file_size,
            "max_files": self.max_files,
            "current_file": str(self.current_file) if self.current_file else None,
            "current_size": self.current_size,
            "total_files": len(log_files),
            "total_size": total_size,
        }
