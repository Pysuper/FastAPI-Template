import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.security.core.constants import AuditEventType
from core.security.core.exceptions import AuditLogError


class AuditEvent:
    """审计事件"""

    def __init__(
        self,
        event_type: AuditEventType,
        user_id: str,
        action: str,
        resource: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        self.event_type = event_type
        self.user_id = user_id
        self.action = action
        self.resource = resource
        self.status = status
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "status": self.status,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """从字典创建实例"""
        return cls(
            event_type=AuditEventType(data["event_type"]),
            user_id=data["user_id"],
            action=data["action"],
            resource=data["resource"],
            status=data["status"],
            details=data["details"],
            ip_address=data["ip_address"],
            user_agent=data["user_agent"],
        )


class BaseAuditLogger(ABC):
    """审计日志记录器基类"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def log_event(self, event: AuditEvent) -> None:
        """记录审计事件"""
        pass

    @abstractmethod
    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """获取审计事件"""
        pass


class FileAuditLogger(BaseAuditLogger):
    """文件审计日志记录器"""

    def __init__(self, log_file: str):
        super().__init__()
        self.log_file = log_file

    def log_event(self, event: AuditEvent) -> None:
        """记录审计事件到文件"""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            raise AuditLogError(f"写入审计日志失败: {str(e)}")

    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """从文件读取审计事件"""
        events = []
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    event_dict = json.loads(line.strip())
                    event = AuditEvent.from_dict(event_dict)

                    # 应用过滤条件
                    if start_time and event.timestamp < start_time:
                        continue
                    if end_time and event.timestamp > end_time:
                        continue
                    if event_type and event.event_type != event_type:
                        continue
                    if user_id and event.user_id != user_id:
                        continue
                    if resource and event.resource != resource:
                        continue
                    if status and event.status != status:
                        continue

                    events.append(event)

            # 应用分页
            return events[offset : offset + limit]
        except Exception as e:
            raise AuditLogError(f"读取审计日志失败: {str(e)}")


class ConsoleAuditLogger(BaseAuditLogger):
    """控制台审计日志记录器"""

    def log_event(self, event: AuditEvent) -> None:
        """记录审计事件到控制台"""
        self.logger.info(json.dumps(event.to_dict(), indent=2))

    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """控制台记录器不支持获取历史事件"""
        return []


class AuditManager:
    """审计管理器"""

    def __init__(self, logger: BaseAuditLogger):
        self.logger = logger

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        action: str,
        resource: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """记录审计事件"""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            action=action,
            resource=resource,
            status=status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.logger.log_event(event)

    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """获取审计事件"""
        return self.logger.get_events(
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            status=status,
            limit=limit,
            offset=offset,
        )
