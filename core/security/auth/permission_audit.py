"""
权限审计服务
跟踪权限变更和访问记录
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from models import AuditLogRecord, Permission
from fastapi import Request
from sqlalchemy.exc import DatabaseError

from core.middlewares.audit import AuditLog, audit_logger, audit_manager


class PermissionAuditService:
    """
    权限审计服务
    记录权限相关的操作日志
    """

    async def log_permission_grant(
        self,
        user_id: str,
        target_id: str,
        permissions: List[Permission],
        operator_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录授予权限操作
        :param user_id: 被授权用户ID
        :param target_id: 目标资源ID
        :param permissions: 授予的权限列表
        :param operator_id: 操作者ID
        :param metadata: 元数据
        """
        permission_strs = [p.to_string() for p in permissions]

        await audit_manager.log_event(
            event_type="permission_grant",
            action="grant",
            resource=f"user:{user_id}",
            user_id=operator_id,
            status="success",
            metadata={
                "target_id": target_id,
                "permissions": permission_strs,
                "operator_id": operator_id,
                **(metadata or {}),
            },
        )

    async def log_permission_revoke(
        self,
        user_id: str,
        target_id: str,
        permissions: List[Permission],
        operator_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录撤销权限操作
        :param user_id: 被撤权用户ID
        :param target_id: 目标资源ID
        :param permissions: 撤销的权限列表
        :param operator_id: 操作者ID
        :param metadata: 元数据
        """
        permission_strs = [p.to_string() for p in permissions]

        await audit_manager.log_event(
            event_type="permission_revoke",
            action="revoke",
            resource=f"user:{user_id}",
            user_id=operator_id,
            status="success",
            metadata={
                "target_id": target_id,
                "permissions": permission_strs,
                "operator_id": operator_id,
                **(metadata or {}),
            },
        )

    async def log_role_assignment(
        self,
        user_id: str,
        role: str,
        operator_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录角色分配操作
        :param user_id: 被分配用户ID
        :param role: 角色名称
        :param operator_id: 操作者ID
        :param metadata: 元数据
        """
        await audit_manager.log_event(
            event_type="role_assignment",
            action="assign",
            resource=f"user:{user_id}",
            user_id=operator_id,
            status="success",
            metadata={"role": role, "operator_id": operator_id, **(metadata or {})},
        )

    async def log_role_removal(
        self,
        user_id: str,
        role: str,
        operator_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录角色移除操作
        :param user_id: 被移除用户ID
        :param role: 角色名称
        :param operator_id: 操作者ID
        :param metadata: 元数据
        """
        await audit_manager.log_event(
            event_type="role_removal",
            action="remove",
            resource=f"user:{user_id}",
            user_id=operator_id,
            status="success",
            metadata={"role": role, "operator_id": operator_id, **(metadata or {})},
        )

    async def log_permission_check(
        self,
        request: Request,
        permission: Permission,
        granted: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录权限检查操作
        :param request: 请求对象
        :param permission: 检查的权限
        :param granted: 是否通过
        :param metadata: 元数据
        """
        user = getattr(request.state, "user", None)
        user_id = user["id"] if user else None

        await audit_manager.log_event(
            event_type="permission_check",
            action="check",
            resource=permission.to_string(),
            user_id=user_id,
            status="success" if granted else "denied",
            metadata={
                "permission": permission.to_string(),
                "granted": granted,
                "request_path": request.url.path,
                "request_method": request.method,
                **(metadata or {}),
            },
        )

    async def log_permission_error(
        self,
        user_id: Optional[str],
        error_type: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录权限错误
        :param user_id: 用户ID
        :param error_type: 错误类型
        :param error_message: 错误消息
        :param metadata: 元数据
        """
        await audit_manager.log_event(
            event_type="permission_error",
            action="error",
            resource=f"user:{user_id}" if user_id else "system",
            user_id=user_id,
            status="error",
            metadata={"error_type": error_type, "error_message": error_message, **(metadata or {})},
        )

    async def get_user_permission_history(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """
        获取用户权限变更历史
        :param user_id: 用户ID
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return: 审计日志列表
        """
        try:
            # 构建查询条件
            conditions = [
                AuditLogRecord.user_id == user_id,
                AuditLogRecord.event_type.in_(["permission_grant", "permission_revoke", "permission_check"]),
            ]

            if start_time:
                conditions.append(AuditLogRecord.timestamp >= start_time)
            if end_time:
                conditions.append(AuditLogRecord.timestamp <= end_time)

            # 从数据库查询记录
            async with audit_manager.db.session() as session:
                query = AuditLogRecord.__table__.select().where(*conditions).order_by(AuditLogRecord.timestamp.desc())

                result = await session.execute(query)
                records = result.fetchall()

                # 转换为AuditLog对象列表
                audit_logs = []
                for record in records:
                    audit_log = AuditLog(
                        timestamp=record.timestamp,
                        event_type=record.event_type,
                        user_id=record.user_id,
                        ip_address=record.ip_address,
                        resource=record.resource,
                        action=record.action,
                        status=record.status,
                        request_id=record.request_id,
                        request_method=record.request_method,
                        request_path=record.request_path,
                        request_query=record.request_query,
                        request_body=record.request_body,
                        response_status=record.response_status,
                        response_body=record.response_body,
                        error_message=record.error_message,
                        metadata=record.metadata,
                    )
                    audit_logs.append(audit_log)

                return audit_logs

        except Exception as e:
            audit_logger.error(f"获取用户权限历史失败: {str(e)}")
            raise DatabaseError(message="获取权限历史记录失败", details={"error": str(e)})


# 创建权限审计服务实例
permission_audit = PermissionAuditService()

# 导出权限审计服务
__all__ = ["permission_audit"]


class AuditLogger:
    pass
