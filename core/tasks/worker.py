import os
from datetime import datetime, timedelta
from pathlib import Path

from celery import Celery
from celery.signals import worker_ready, worker_shutting_down
from celery.utils.log import get_task_logger
from core.models.audit_log import AuditLogRecord
from pydantic.v1 import EmailError

from config.manager import config_manager
from core.config.setting import settings
from security.audit import audit_manager
from tasks.email_client import EmailClient, EmailMessage

logger = get_task_logger(__name__)


# 创建Celery实例
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery配置
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,
    task_reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
)

celery_app.autodiscover_tasks(["app.core.tasks"], force=True)


@worker_ready.connect
def on_worker_ready(**_):
    """Worker就绪时的回调"""
    logger.info("Celery worker is ready")


@worker_shutting_down.connect
def on_worker_shutting_down(**_):
    """Worker关闭时的回调"""
    logger.info("Celery worker is shutting down")


@celery_app.task(name="example_task")
def example_task(x: int, y: int) -> int:
    """示例任务：计算两个数的和"""
    logger.info(f"Executing example task with params: x={x}, y={y}")
    result = x + y
    logger.info(f"Example task result: {result}")
    return result


@celery_app.task(
    bind=True,
    name="example.add",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def add(self, x: int, y: int) -> int:
    """示例任务：加法"""
    try:
        return x + y
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="tasks.send_email",
    max_retries=3,
    default_retry_delay=300,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def send_email(
    self,
    to_email: str,
    subject: str,
    content: str,
    template_id: str = None,
    template_data: dict = None,
) -> bool:
    """发送邮件任务"""
    try:
        # 获取邮件配置
        email_config = config_manager.get_email_config()

        # 创建邮件客户端
        email_client = EmailClient(
            host=email_config.SMTP_HOST,
            port=email_config.SMTP_PORT,
            username=email_config.SMTP_USER,
            password=email_config.SMTP_PASSWORD,
            use_tls=email_config.USE_TLS,
            timeout=email_config.TIMEOUT,
        )

        # 如果使用模板
        if template_id and template_data:
            # 获取模板内容
            template = email_client.get_template(template_id)
            # 渲染模板
            content = template.render(**template_data)

        # 构建邮件消息
        message = EmailMessage(
            subject=subject,
            body=content,
            from_email=email_config.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )

        # 发送邮件
        email_client.send(message)

        # 记录审计日志
        audit_manager.log_event(
            event_type="email_sent",
            action="send",
            resource=f"email:{to_email}",
            status="success",
            metadata={"subject": subject, "template_id": template_id},
        )

        logger.info(f"Successfully sent email to {to_email}")
        return True

    except EmailError as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        # 记录失败审计
        audit_manager.log_event(
            event_type="email_sent",
            action="send",
            resource=f"email:{to_email}",
            status="error",
            metadata={"error": str(e), "subject": subject},
        )
        raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="tasks.process_file",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def process_file(self, file_path: str, options: dict = None) -> dict:
    """处理文件任务"""
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 获取文件信息
        file_info = {
            "size": os.path.getsize(file_path),
            "created_time": datetime.fromtimestamp(os.path.getctime(file_path)),
            "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)),
        }

        # 处理选项
        options = options or {}
        process_type = options.get("process_type", "default")

        # 根据文件类型进行处理
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in [".txt", ".log", ".csv"]:
            # 文本文件处理
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 进行文本处理...
                processed_content = content.strip()

            # 保存处理结果
            output_path = f"{file_path}.processed"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(processed_content)

        elif file_ext in [".jpg", ".png", ".gif"]:
            # 图片处理
            from PIL import Image

            img = Image.open(file_path)

            # 进行图片处理...
            if process_type == "resize":
                width = options.get("width", 800)
                height = options.get("height", 600)
                img = img.resize((width, height))

            # 保存处理结果
            output_path = f"{file_path}.processed{file_ext}"
            img.save(output_path)

        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

        # 记录审计日志
        audit_manager.log_event(
            event_type="file_processed",
            action="process",
            resource=f"file:{file_path}",
            status="success",
            metadata={"file_info": file_info, "process_type": process_type, "options": options},
        )

        logger.info(f"Successfully processed file: {file_path}")
        return {
            "status": "success",
            "file_path": file_path,
            "output_path": output_path,
            "file_info": file_info,
            "process_type": process_type,
        }

    except Exception as e:
        logger.error(f"Failed to process file: {str(e)}")
        # 记录失败审计
        audit_manager.log_event(
            event_type="file_processed",
            action="process",
            resource=f"file:{file_path}",
            status="error",
            metadata={"error": str(e), "options": options},
        )
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="tasks.generate_report",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
async def generate_report(self, report_type: str, params: dict) -> dict:
    """生成报告任务"""
    try:
        logger.info(f"开始生成报告: {report_type}")

        # 根据报告类型生成不同的报告
        if report_type == "user_activity":
            # 生成用户活动报告
            start_time = params.get("start_time")
            end_time = params.get("end_time")
            user_id = params.get("user_id")

            # 获取用户活动历史
            audit_logs = await audit_manager.get_user_permission_history(
                user_id=user_id, start_time=start_time, end_time=end_time
            )

            # 生成报告内容
            report_data = {
                "user_id": user_id,
                "period": {"start": start_time, "end": end_time},
                "activities": [log.dict() for log in audit_logs],
            }

        elif report_type == "system_audit":
            # 生成系统审计报告
            days = params.get("days", 7)
            event_types = params.get("event_types", ["permission_check", "permission_grant"])

            # 查询审计日志
            async with audit_manager.db.session() as session:
                query = (
                    AuditLogRecord.__table__.select()
                    .where(
                        AuditLogRecord.event_type.in_(event_types),
                        AuditLogRecord.timestamp >= datetime.now() - timedelta(days=days),
                    )
                    .order_by(AuditLogRecord.timestamp.desc())
                )

                result = await session.execute(query)
                records = result.fetchall()

                report_data = {
                    "period": f"最近{days}天",
                    "event_types": event_types,
                    "total_records": len(records),
                    "records": [dict(r) for r in records],
                }

        else:
            raise ValueError(f"不支持的报告类型: {report_type}")

        # 记录审计日志
        await audit_manager.log_event(
            event_type="report_generated",
            action="generate",
            resource=f"report:{report_type}",
            status="success",
            metadata={"report_type": report_type, "params": params},
        )

        logger.info(f"报告生成成功: {report_type}")
        return {"status": "success", "report_type": report_type, "data": report_data}

    except Exception as e:
        logger.error(f"生成报告失败: {str(e)}")
        # 记录失败审计
        await audit_manager.log_event(
            event_type="report_generated",
            action="generate",
            resource=f"report:{report_type}",
            status="error",
            metadata={"error": str(e), "params": params},
        )
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="tasks.cleanup",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
async def cleanup(self, resource_type: str, older_than_days: int = 30) -> dict:
    """清理任务"""
    try:
        logger.info(f"开始清理 {resource_type} 数据")

        if resource_type == "audit_logs":
            # 清理审计日志
            await audit_manager.cleanup_old_logs()

        elif resource_type == "temp_files":
            # 清理临时文件
            temp_dir = config_manager.get("TEMP_DIR", "temp")
            expiry_date = datetime.now() - timedelta(days=older_than_days)

            # 遍历临时目录
            for file_path in Path(temp_dir).glob("*"):
                if file_path.is_file():
                    # 获取文件修改时间
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < expiry_date:
                        try:
                            file_path.unlink()
                            logger.info(f"已删除过期文件: {file_path}")
                        except OSError as e:
                            logger.error(f"删除文件失败: {file_path}, 错误: {e}")

        else:
            raise ValueError(f"不支持的资源类型: {resource_type}")

        # 记录审计日志
        await audit_manager.log_event(
            event_type="resource_cleanup",
            action="cleanup",
            resource=resource_type,
            status="success",
            metadata={"older_than_days": older_than_days},
        )

        logger.info(f"清理任务完成: {resource_type}")
        return {"status": "success", "resource_type": resource_type, "older_than_days": older_than_days}

    except Exception as e:
        logger.error(f"清理任务失败: {str(e)}")
        # 记录失败审计
        await audit_manager.log_event(
            event_type="resource_cleanup",
            action="cleanup",
            resource=resource_type,
            status="error",
            metadata={"error": str(e), "older_than_days": older_than_days},
        )
        raise self.retry(exc=e)
