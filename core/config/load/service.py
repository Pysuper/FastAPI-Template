# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：service.py
@Author  ：PySuper
@Date    ：2024/12/26 09:57 
@Desc    ：Speedy service.py
"""
from typing import List

from core.config.load.base import BaseConfig


class ServiceConfig(BaseConfig):
    """
    服务发现配置
    """

    SERVICE_NAME: str = "api-rocket"
    SERVICE_DISCOVERY_PROVIDER: str = "consul"  # consul, etcd, eureka
    SERVICE_DISCOVERY_HOST: str = "localhost"
    SERVICE_DISCOVERY_PORT: int = 8500
    SERVICE_TAGS: List[str] = ["api", "fastapi"]
    SERVICE_CHECK_INTERVAL: str = "10s"
    SERVICE_CHECK_TIMEOUT: str = "5s"
    SERVICE_CHECK_DEREGISTER_AFTER: str = "1m"


class AliYunConfig:
    """
    阿里云配置
    """

    # 阿里云配置（可选）
    ALIYUN_ACCESS_KEY_ID: str | None = None
    ALIYUN_ACCESS_KEY_SECRET: str | None = None

    # 阿里云OSS配置（可选）
    ALIYUN_OSS_ENDPOINT: str | None = None
    ALIYUN_OSS_BUCKET: str | None = None
    ALIYUN_OSS_INTERNAL: bool = False
    ALIYUN_OSS_SECURE: bool = True

    # 阿里云SMS配置（可选）
    ALIYUN_SMS_REGION_ID: str = "cn-hangzhou"
    ALIYUN_SMS_ENDPOINT: str = "dysmsapi.aliyuncs.com"
    ALIYUN_SMS_SIGN_NAME: str | None = None
    ALIYUN_SMS_TEMPLATE_CODE: str | None = None


class TencentConfig:
    """
    腾讯云配置
    """

    # 腾讯云配置（可选）
    TENCENT_SECRET_ID: str | None = None
    TENCENT_SECRET_KEY: str | None = None

    # 腾讯云COS配置（可选）
    TENCENT_COS_REGION: str | None = None
    TENCENT_COS_BUCKET: str | None = None
    TENCENT_COS_SCHEME: str = "https"
    TENCENT_COS_ENDPOINT: str | None = None

    # 腾讯云SMS配置（可选）
    TENCENT_SMS_APP_ID: str | None = None
    TENCENT_SMS_REGION: str = "ap-guangzhou"
    TENCENT_SMS_ENDPOINT: str = "sms.tencentcloudapi.com"
    TENCENT_SMS_SIGN_NAME: str | None = None
    TENCENT_SMS_TEMPLATE_ID: str | None = None


class CephConfig:
    """
    Ceph配置（可选）
    """

    CEPH_ACCESS_KEY: str | None = None
    CEPH_SECRET_KEY: str | None = None
    CEPH_ENDPOINT: str | None = None
    CEPH_BUCKET: str | None = None
    CEPH_SECURE: bool = True
    CEPH_REGION: str = ""
    CEPH_SIGNATURE_VERSION: str = "s3v4"


class MinioConfig:
    """
    MinIO配置（可选）
    """

    MINIO_ENDPOINT: str | None = None
    MINIO_ACCESS_KEY: str | None = None
    MINIO_SECRET_KEY: str | None = None
    MINIO_BUCKET: str | None = None
    MINIO_SECURE: bool = True
    MINIO_REGION: str | None = None


class HttpConfig:
    """
    HTTP客户端配置
    """

    HTTP_TIMEOUT: int = 30
    HTTP_MAX_RETRIES: int = 3
    HTTP_POOL_SIZE: int = 100
    HTTP_RETRY_INTERVAL: int = 1
    HTTP_MAX_REDIRECTS: int = 10
    HTTP_VERIFY_SSL: bool = True


class CORSConfig:
    """
    跨域配置
    """

    CORS_ORIGINS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]


class UtilsConfig:
    # JWT配置
    SECRET_KEY: str = "PySuper"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 监控配置
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"
    METRICS_PORT: int = 9090
    ENABLE_METRICS: bool = True

    # 断路器配置
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CIRCUIT_BREAKER_MAX_FAILURES: int = 3
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 30

    # 国际化配置
    LOCALE_DIR: str = "locales"
    DEFAULT_LOCALE: str = "zh_CN"
    SUPPORTED_LOCALES: List[str] = ["zh_CN", "en_US"]
    FALLBACK_LOCALE: str = "en_US"

    # 备份配置
    BACKUP_DIR: str = "backups"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_COMPRESSION: bool = True
    BACKUP_SCHEDULE: str = "0 0 * * *"  # 每天凌晨
    BACKUP_MAX_SIZE: int = 1024 * 1024 * 1024  # 1GB

    # 灾难恢复配置
    DR_ENABLED: bool = False
    DR_BACKUP_LOCATION: str = "s3://backup"
    DR_BACKUP_FREQUENCY: str = "daily"
    DR_RETENTION_PERIOD: int = 30  # days
    DR_AUTO_FAILOVER: bool = False
    DR_FAILOVER_THRESHOLD: int = 3
