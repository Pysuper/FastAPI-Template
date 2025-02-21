# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：api_audit.py
@Author  ：PySuper
@Date    ：2024-12-25 00:15
@Desc    ：Speedy api_audit
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

from core.config.setting import settings
from core.exceptions.system.database import DatabaseException
from core.middlewares.base import BaseCustomMiddleware
from models import AuditLogRecord
from security.core.encryption import encryption_provider

# 创建审计日志记录器
audit_logger = logging.getLogger(settings.audit.AUDIT_LOGGER)


class AuditLog(BaseModel):
    """审计日志模型"""

    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    ip_address: str
    resource: str
    action: str
    status: str
    request_id: Optional[str]
    request_method: str
    request_path: str
    request_query: Optional[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    response_status: Optional[int]
    response_body: Optional[Dict[str, Any]]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]


class AuditLogManager:
    """
    审计日志管理器
    处理日志记录和存储
    """

    def __init__(self):
        self.config = settings.audit
        self._setup_logger()
        self._sensitive_fields = set(self.config.SENSITIVE_FIELDS)

    def _setup_logger(self) -> None:
        """配置日志记录器"""
        # 创建文件处理器
        handler = logging.FileHandler(self.config.AUDIT_FILE)

        # 设置日志格式
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        # 添加处理器
        audit_logger.addHandler(handler)
        audit_logger.setLevel(logging.INFO)

    def _mask_sensitive_data(
        self, data: Union[Dict[str, Any], List[Any], str, None]
    ) -> Union[Dict[str, Any], List[Any], str, None]:
        """
        遮蔽敏感数据
        :param data: 原始数据
        :return: 遮蔽后的数据
        """
        if data is None:
            return None

        if isinstance(data, str):
            return data

        if isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]

        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if key.lower() in self._sensitive_fields:
                    masked[key] = "*" * 8
                elif isinstance(value, (dict, list)):
                    masked[key] = self._mask_sensitive_data(value)
                else:
                    masked[key] = value
            return masked

        return data

    async def log_request(
        self, request: Request, response: Optional[Response] = None, error: Optional[Exception] = None
    ) -> None:
        """
        记录请求日志
        :param request: 请求对象
        :param response: 响应对象
        :param error: 异常对象
        """
        if not self.config.AUDIT_ENABLED:
            return

        try:
            # 获取请求信息
            timestamp = datetime.now()
            user_id = getattr(request.state, "user", {}).get("id")
            request_id = getattr(request.state, "request_id", None)

            # 获取请求体
            body = None
            if self.config.AUDIT_BODY:
                try:
                    body = await request.json()
                except Exception:
                    body = None

            # 创建审计日志
            audit_log = AuditLog(
                timestamp=timestamp,
                event_type="request",
                user_id=user_id,
                ip_address=request.client.host,
                resource=request.url.path,
                action=request.method,
                status="error" if error else "success",
                request_id=request_id,
                request_method=request.method,
                request_path=str(request.url.path),
                request_query=dict(request.query_params) if self.config.AUDIT_QUERY else None,
                request_body=self._mask_sensitive_data(body) if body else None,
                response_status=response.status_code if response else None,
                response_body=None,  # 响应体需要单独处理
                error_message=str(error) if error else None,
                metadata={"user_agent": request.headers.get("user-agent"), "referer": request.headers.get("referer")},
            )

            # 记录响应体
            if response and self.config.AUDIT_RESPONSE:
                try:
                    response_body = await response.json()
                    audit_log.response_body = self._mask_sensitive_data(response_body)
                except Exception:
                    pass

            # 转换为JSON并记录
            audit_logger.info(audit_log.json())

            # 如果使用数据库存储，异步保存
            if self.config.STORAGE_TYPE == "database":
                asyncio.create_task(self._save_to_database(audit_log))

        except Exception as e:
            audit_logger.error(f"Failed to log audit: {e}")

    async def _save_to_database(self, audit_log: AuditLog) -> None:
        """
        将审计日志保存到数据库
        :param audit_log: 审计日志对象
        """
        try:
            # 将审计日志转换为字典格式
            log_data = audit_log.dict()

            # 连接数据库
            async with self.db.session() as session:
                # 创建审计日志记录
                audit_record = AuditLogRecord(
                    timestamp=log_data["timestamp"],
                    event_type=log_data["event_type"],
                    user_id=log_data["user_id"],
                    ip_address=log_data["ip_address"],
                    resource=log_data["resource"],
                    action=log_data["action"],
                    status=log_data["status"],
                    request_id=log_data["request_id"],
                    request_method=log_data["request_method"],
                    request_path=log_data["request_path"],
                    request_query=log_data["request_query"],
                    request_body=log_data["request_body"],
                    response_status=log_data["response_status"],
                    response_body=log_data["response_body"],
                    error_message=log_data["error_message"],
                    metadata=log_data["metadata"],
                )

                # 添加并提交到数据库
                session.add(audit_record)
                await session.commit()

        except Exception as e:
            audit_logger.error(f"保存审计日志到数据库失败: {str(e)}")
            raise DatabaseException(message="保存审计日志失败", details={"error": str(e)})

    async def log_event(
        self,
        event_type: str,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录自定义事件
        :param event_type: 事件类型
        :param action: 操作
        :param resource: 资源
        :param user_id: 用户ID
        :param status: 状态
        :param metadata: 元数据
        """
        if not self.config.AUDIT_ENABLED:
            return

        try:
            audit_log = AuditLog(
                timestamp=datetime.now(),
                event_type=event_type,
                user_id=user_id,
                ip_address="system",
                resource=resource,
                action=action,
                status=status,
                request_id=None,
                request_method="system",
                request_path="",
                metadata=self._mask_sensitive_data(metadata),
            )

            # 记录日志
            audit_logger.info(audit_log.json())

            # 如果使用数据库存储，异步保存
            if self.config.STORAGE_TYPE == "database":
                asyncio.create_task(self._save_to_database(audit_log))

        except Exception as e:
            audit_logger.error(f"Failed to log event: {e}")

    async def cleanup_old_logs(self) -> None:
        """清理过期的审计日志"""
        if not self.config.RETENTION_DAYS:
            return

        try:
            # 如果使用文件存储，清理旧文件
            if self.config.STORAGE_TYPE == "file":
                # 获取日志文件目录
                log_dir = self.config.LOG_DIR
                if not log_dir:
                    return

                # 计算过期时间
                expiry_date = datetime.now() - timedelta(days=self.config.RETENTION_DAYS)

                # 遍历日志文件
                for file_path in log_dir.glob("*.log"):
                    # 获取文件修改时间
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < expiry_date:
                        try:
                            file_path.unlink()
                            audit_logger.info(f"已删除过期日志文件: {file_path}")
                        except OSError as e:
                            audit_logger.error(f"删除日志文件失败: {file_path}, 错误: {e}")

            # 如果使用数据库存储，清理旧记录
            elif self.config.STORAGE_TYPE == "database":
                # 计算过期时间
                expiry_date = datetime.now() - timedelta(days=self.config.RETENTION_DAYS)

                # 删除过期记录
                async with self.db_session() as session:
                    delete_stmt = AuditLogRecord.__table__.delete().where(AuditLogRecord.timestamp < expiry_date)
                    result = await session.execute(delete_stmt)
                    await session.commit()

                    deleted_count = result.rowcount
                    audit_logger.info(f"已删除 {deleted_count} 条过期审计日志记录")

        except Exception as e:
            audit_logger.error(f"清理过期日志失败: {e}")
            raise DatabaseException(message="清理审计日志失败", details={"error": str(e)})



class APIAuditMiddleware(BaseCustomMiddleware):
    """
    API访问审计中间件
    实现API访问日志记录和审计
    """

    def __init__(self, app):
        super().__init__(app)
        self.config = settings.audit
        self.sensitive_fields = set(self.config.SENSITIVE_FIELDS)
        print(" ✅ APIAuditMiddleware")

    async def _get_request_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        获取请求体
        处理敏感数据
        """
        if request.method not in ("POST", "PUT", "PATCH"):
            return None

        try:
            body = await request.json()
            if isinstance(body, dict):
                # 加密敏感字段
                return encryption_provider.encrypt_dict(body, self.sensitive_fields)
            return body
        except:
            return None

    async def _get_response_body(self, response: Response) -> Optional[Dict[str, Any]]:
        """
        获取响应体
        处理敏感数据
        """
        try:
            body = await response.json()
            if isinstance(body, dict):
                # 加密敏感字段
                return encryption_provider.encrypt_dict(body, self.sensitive_fields)
            return body
        except:
            return None

    def _should_audit(self, request: Request) -> bool:
        """判断是否需要审计"""
        # 检查是否启用审计
        if not self.config.AUDIT_ENABLED:
            return False

        # 检查是否是审计路径
        path = request.url.path
        if path.startswith("/metrics") or path.startswith("/health"):
            return False

        return True

    def _get_user_info(self, request: Request) -> Dict[str, Any]:
        """获取用户信息"""
        user = getattr(request.state, "user", None)
        if user:
            return {"user_id": user.get("id"), "username": user.get("username"), "roles": user.get("roles", []),}
        return {}

    def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """获取请求信息"""
        return {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {k: v for k, v in request.headers.items() if k.lower() in self.config.AUDIT_HEADERS},
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
        }

    async def _log_request(
        self,
        request: Request,
        response: Optional[Response] = None,
        error: Optional[Exception] = None,
        duration: Optional[float] = None,
    ) -> None:
        """
        记录请求审计日志
        :param request: 请求对象
        :param response: 响应对象
        :param error: 异常对象
        :param duration: 处理时间(秒)
        """
        # 获取基本信息
        user_info = self._get_user_info(request)
        request_info = self._get_request_info(request)

        # 获取请求体
        if self.config.AUDIT_BODY:
            request_body = await self._get_request_body(request)
            if request_body:
                request_info["body"] = request_body

        # 构建审计数据
        audit_data = {
            "timestamp": time.time(),
            "request": request_info,
            "user": user_info,
        }

        # 添加响应信息
        if response:
            audit_data["response"] = {"status_code": response.status_code, "headers": dict(response.headers),}

            # 获取响应体
            if self.config.AUDIT_RESPONSE:
                response_body = await self._get_response_body(response)
                if response_body:
                    audit_data["response"]["body"] = response_body

        # 添加错误信息
        if error:
            audit_data["error"] = {"type": type(error).__name__, "message": str(error)}

        # 添加处理时间
        if duration is not None:
            audit_data["duration"] = duration

        # 记录审计日志
        await audit_manager.log_event(
            event_type="api_access",
            action=request.method.lower(),
            resource=request.url.path,
            user_id=user_info.get("user_id"),
            status="error" if error else "success",
            metadata=audit_data,
        )

    async def dispatch(self, request: Request, call_next):
        if not self._should_audit(request):
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()

        try:
            # 处理请求
            response = await call_next(request)

            # 计算处理时间
            duration = time.time() - start_time

            # 记录审计日志
            await self._log_request(request, response=response, duration=duration)

            return response

        except Exception as e:
            # 计算处理时间
            duration = time.time() - start_time

            # 记录审计日志
            await self._log_request(request, error=e, duration=duration)

            raise


# 创建审计日志管理器实例
audit_manager = AuditLogManager()

# 导出审计日志管理器
__all__ = ["audit_manager"]