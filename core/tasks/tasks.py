# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：tasks.py
@Author  ：PySuper
@Date    ：2024/12/30 10:34 
@Desc    ：任务定义模块

提供系统中所有的异步任务定义，包含以下特性：
    1. 邮件发送任务
    2. 报告生成任务
    3. 数据库备份任务
    4. 文件清理任务
    5. 缓存同步任务
    6. 定时任务配置
"""

import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

from celery import Celery
from celery.schedules import crontab

from core.tasks.base import BaseTask

# 创建Celery实例
celery = Celery("project_name", broker="redis://localhost:your_port/1", backend="redis://localhost:your_port/2")

# Celery配置
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 任务超时时间1小时
    worker_max_tasks_per_child=200,  # 每个worker最多执行200个任务后重启
    worker_prefetch_multiplier=4,  # 每个worker预取4个任务
    task_default_queue="default",  # 默认队列
    task_routes={
        "tasks.send_email": {"queue": "email"},
        "tasks.generate_report": {"queue": "report"},
        "tasks.backup_database": {"queue": "backup"},
        "tasks.clean_expired_files": {"queue": "maintenance"},
        "tasks.sync_cache": {"queue": "cache"},
    },
)

# 邮件配置
EMAIL_CONFIG = {
    "host": os.getenv("EMAIL_HOST", "smtp.example.com"),
    "port": int(os.getenv("EMAIL_PORT", "587")),
    "user": os.getenv("EMAIL_HOST_USER", "user@example.com"),
    "password": os.getenv("EMAIL_HOST_PASSWORD", "password"),
    "use_tls": True,
}


@celery.task(name="tasks.send_email", base=BaseTask, bind=True, max_retries=3, default_retry_delay=300)  # 5分钟后重试
def send_email(
    self,
    to_email: str,
    subject: str,
    content: str,
    is_html: bool = False,
    attachments: Optional[Dict[str, bytes]] = None,
) -> Dict[str, Any]:
    """
    发送邮件任务

    Args:
        to_email: 收件人邮箱
        subject: 邮件主题
        content: 邮件内容
        is_html: 是否为HTML格式
        attachments: 附件字典，键为文件名，值为文件内容

    Returns:
        Dict[str, Any]: 任务执行结果
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["user"]
        msg["To"] = to_email
        msg["Subject"] = subject

        # 添加邮件正文
        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(content, content_type, "utf-8"))

        # 添加附件
        if attachments:
            for filename, content in attachments.items():
                attachment = MIMEText(content, "base64", "utf-8")
                attachment["Content-Type"] = "application/octet-stream"
                attachment["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(attachment)

        # 发送邮件
        with smtplib.SMTP(EMAIL_CONFIG["host"], EMAIL_CONFIG["port"]) as server:
            if EMAIL_CONFIG["use_tls"]:
                server.starttls()
            server.login(EMAIL_CONFIG["user"], EMAIL_CONFIG["password"])
            server.send_message(msg)

        self.logger.info(f"Email sent successfully to {to_email}")
        return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        self.logger.error(f"Failed to send email: {str(e)}")
        self.retry(exc=e)


@celery.task(name="tasks.generate_report", base=BaseTask, bind=True, max_retries=3)
def generate_report(self, report_type: str, params: Dict[str, Any], output_format: str = "pdf") -> Dict[str, Any]:
    """
    生成报告任务

    Args:
        report_type: 报告类型
        params: 报告参数
        output_format: 输出格式

    Returns:
        Dict[str, Any]: 任务执行结果
    """
    try:
        # 根据报告类型生成不同的报告
        report_funcs = {
            "student_performance": generate_student_performance_report,
            "course_statistics": generate_course_statistics_report,
            "attendance_summary": generate_attendance_summary_report,
        }

        if report_type not in report_funcs:
            raise ValueError(f"Unknown report type: {report_type}")

        result = report_funcs[report_type](params)
        result["output_format"] = output_format
        return result

    except Exception as e:
        self.logger.error(f"Failed to generate report: {str(e)}")
        self.retry(exc=e)


@celery.task(name="tasks.backup_database", base=BaseTask, bind=True)
def backup_database(self) -> Dict[str, Any]:
    """
    数据库备份任务

    Returns:
        Dict[str, Any]: 任务执行结果
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        backup_file = backup_dir / f"backup_{timestamp}.sql"

        # 执行数据库备份命令
        result = os.system(f"pg_dump -U postgres project_name > {backup_file}")
        if result != 0:
            raise RuntimeError("Database backup command failed")

        self.logger.info(f"Database backup created: {backup_file}")
        return {"status": "success", "backup_file": str(backup_file), "timestamp": timestamp}
    except Exception as e:
        self.logger.error(f"Failed to backup database: {str(e)}")
        raise


@celery.task(name="tasks.clean_expired_files", base=BaseTask, bind=True)
def clean_expired_files(self, max_age_days: int = 1, directories: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    清理过期文件任务

    Args:
        max_age_days: 文件最大保留天数
        directories: 要清理的目录列表

    Returns:
        Dict[str, Any]: 任务执行结果
    """
    try:
        directories = directories or ["temp", "logs", "uploads"]
        removed_files = []

        for dir_name in directories:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                continue

            for file_path in dir_path.glob("**/*"):
                if not file_path.is_file():
                    continue

                # 检查文件是否过期
                if datetime.fromtimestamp(file_path.stat().st_ctime) < datetime.now() - timedelta(days=max_age_days):
                    file_path.unlink()
                    removed_files.append(str(file_path))
                    self.logger.info(f"Removed expired file: {file_path}")

        return {"status": "success", "message": "Expired files cleaned", "removed_files": removed_files}
    except Exception as e:
        self.logger.error(f"Failed to clean expired files: {str(e)}")
        raise


@celery.task(name="tasks.sync_cache", base=BaseTask, bind=True)
def sync_cache(self) -> Dict[str, Any]:
    """
    同步缓存任务

    Returns:
        Dict[str, Any]: 任务执行结果
    """
    try:
        # TODO: 实现缓存同步逻辑
        return {"status": "success", "message": "Cache synchronized", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        self.logger.error(f"Failed to sync cache: {str(e)}")
        raise


# 定时任务配置
celery.conf.beat_schedule = {
    "backup-database-daily": {
        "task": "tasks.backup_database",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点执行
    },
    "clean-expired-files-hourly": {
        "task": "tasks.clean_expired_files",
        "schedule": crontab(minute=0),  # 每小时整点执行
    },
    "sync-cache-every-5-minutes": {
        "task": "tasks.sync_cache",
        "schedule": timedelta(minutes=5),  # 每5分钟执行一次
    },
}


# 辅助函数
def generate_student_performance_report(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成学生表现报告

    Args:
        params: 报告参数

    Returns:
        Dict[str, Any]: 报告生成结果
    """
    # TODO: 实现学生表现报告生成逻辑
    return {"status": "success", "message": "Student performance report generated"}


def generate_course_statistics_report(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成课程统计报告

    Args:
        params: 报告参数

    Returns:
        Dict[str, Any]: 报告生成结果
    """
    # TODO: 实现课程统计报告生成逻辑
    return {"status": "success", "message": "Course statistics report generated"}


def generate_attendance_summary_report(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成出勤汇总报告

    Args:
        params: 报告参数

    Returns:
        Dict[str, Any]: 报告生成结果
    """
    # TODO: 实现出勤汇总报告生成逻辑
    return {"status": "success", "message": "Attendance summary report generated"}


# 导出
__all__ = [
    "celery",
    "send_email",
    "generate_report",
    "backup_database",
    "clean_expired_files",
    "sync_cache",
]
