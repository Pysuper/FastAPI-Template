"""
监控配置模块
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MonitorConfig(BaseModel):
    """监控配置"""

    # 基础配置
    enabled: bool = Field(default=True, description="是否启用监控")
    interval: float = Field(default=60.0, description="监控间隔(秒)")
    max_metrics: int = Field(default=1000, description="最大指标数量")

    # 连接配置
    connection_enabled: bool = Field(default=True, description="是否启用连接监控")
    max_connections: int = Field(default=100, description="最大连接数")
    connection_timeout: float = Field(default=30.0, description="连接超时时间(秒)")

    # 查询配置
    query_enabled: bool = Field(default=True, description="是否启用查询监控")
    max_query_time: float = Field(default=1.0, description="最大查询时间(秒)")
    max_slow_queries: int = Field(default=100, description="最大慢查询数量")

    # 事务配置
    transaction_enabled: bool = Field(default=True, description="是否启用事务监控")
    max_transaction_time: float = Field(default=5.0, description="最大事务时间(秒)")
    max_rollback_rate: float = Field(default=0.1, description="最大回滚率")

    # 缓存配置
    cache_enabled: bool = Field(default=True, description="是否启用缓存监控")
    max_cache_size: int = Field(default=1000, description="最大缓存大小")
    min_hit_rate: float = Field(default=0.5, description="最小命中率")

    # 限流配置
    rate_limit_enabled: bool = Field(default=True, description="是否启用限流监控")
    max_requests: int = Field(default=100, description="最大请求数")
    time_window: float = Field(default=60.0, description="时间窗口(秒)")

    # 熔断配置
    circuit_breaker_enabled: bool = Field(default=True, description="是否启用熔断监控")
    failure_threshold: int = Field(default=5, description="失败阈值")
    reset_timeout: float = Field(default=60.0, description="重置超时时间(秒)")

    # 重试配置
    retry_enabled: bool = Field(default=True, description="是否启用重试监控")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟(秒)")
    retry_backoff: float = Field(default=2.0, description="重试退避系数")

    # 超时配置
    timeout_enabled: bool = Field(default=True, description="是否启用超时监控")
    request_timeout: float = Field(default=30.0, description="请求超时时间(秒)")
    max_timeout_rate: float = Field(default=0.1, description="最大超时率")

    # 告警配置
    alert_enabled: bool = Field(default=True, description="是否启用告警")
    alert_interval: float = Field(default=300.0, description="告警间隔(秒)")
    alert_channels: List[str] = Field(default=["email"], description="告警通道")

    # 日志配置
    log_enabled: bool = Field(default=True, description="是否启用日志")
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式",
    )

    # 指标配置
    metrics_enabled: bool = Field(default=True, description="是否启用指标")
    metrics_path: str = Field(default="/metrics", description="指标路径")
    metrics_format: str = Field(default="prometheus", description="指标格式")

    # 追踪配置
    trace_enabled: bool = Field(default=True, description="是否启用追踪")
    trace_sample_rate: float = Field(default=0.1, description="追踪采样率")
    trace_service_name: str = Field(default="project_name", description="追踪服务名称")

    # 导出配置
    export_enabled: bool = Field(default=True, description="是否启用导出")
    export_interval: float = Field(default=60.0, description="导出间隔(秒)")
    export_path: str = Field(default="/tmp/monitor", description="导出路径")

    # 存储配置
    storage_enabled: bool = Field(default=True, description="是否启用存储")
    storage_type: str = Field(default="file", description="存储类型")
    storage_path: str = Field(default="/tmp/monitor", description="存储路径")
    storage_retention: int = Field(default=7, description="存储保留天数")

    # 聚合配置
    aggregation_enabled: bool = Field(default=True, description="是否启用聚合")
    aggregation_interval: float = Field(default=60.0, description="聚合间隔(秒)")
    aggregation_functions: List[str] = Field(
        default=["avg", "max", "min", "sum", "count"],
        description="聚合函数",
    )

    # 过滤配置
    filter_enabled: bool = Field(default=True, description="是否启用过滤")
    filter_rules: List[Dict[str, Any]] = Field(default=[], description="过滤规则")

    # 采样配置
    sampling_enabled: bool = Field(default=True, description="是否启用采样")
    sampling_rate: float = Field(default=0.1, description="采样率")
    sampling_rules: List[Dict[str, Any]] = Field(default=[], description="采样规则")

    # 标签配置
    label_enabled: bool = Field(default=True, description="是否启用标签")
    label_rules: List[Dict[str, Any]] = Field(default=[], description="标签规则")

    # 分析配置
    analysis_enabled: bool = Field(default=True, description="是否启用分析")
    analysis_interval: float = Field(default=300.0, description="分析间隔(秒)")
    analysis_rules: List[Dict[str, Any]] = Field(default=[], description="分析规则")

    # 报告配置
    report_enabled: bool = Field(default=True, description="是否启用报告")
    report_interval: float = Field(default=86400.0, description="报告间隔(秒)")
    report_template: str = Field(default="default", description="报告模板")
    report_format: str = Field(default="html", description="报告格式")

    # 清理配置
    cleanup_enabled: bool = Field(default=True, description="是否启用清理")
    cleanup_interval: float = Field(default=86400.0, description="清理间隔(秒)")
    cleanup_rules: List[Dict[str, Any]] = Field(default=[], description="清理规则")

    # 备份配置
    backup_enabled: bool = Field(default=True, description="是否启用备份")
    backup_interval: float = Field(default=86400.0, description="备份间隔(秒)")
    backup_path: str = Field(default="/tmp/monitor/backup", description="备份路径")
    backup_retention: int = Field(default=7, description="备份保留天数")

    # 恢复配置
    recovery_enabled: bool = Field(default=True, description="是否启用恢复")
    recovery_path: str = Field(default="/tmp/monitor/recovery", description="恢复路径")
    recovery_rules: List[Dict[str, Any]] = Field(default=[], description="恢复规则")

    # 安全配置
    security_enabled: bool = Field(default=True, description="是否启用安全")
    security_rules: List[Dict[str, Any]] = Field(default=[], description="安全规则")

    # 授权配置
    auth_enabled: bool = Field(default=True, description="是否启用授权")
    auth_rules: List[Dict[str, Any]] = Field(default=[], description="授权规则")

    # 加密配置
    encryption_enabled: bool = Field(default=True, description="是否启用加密")
    encryption_key: str = Field(default="", description="加密密钥")
    encryption_algorithm: str = Field(default="AES", description="加密算法")

    # 压缩配置
    compression_enabled: bool = Field(default=True, description="是否启用压缩")
    compression_algorithm: str = Field(default="gzip", description="压缩算法")
    compression_level: int = Field(default=6, description="压缩级别")

    # 验证配置
    validation_enabled: bool = Field(default=True, description="是否启用验证")
    validation_rules: List[Dict[str, Any]] = Field(default=[], description="验证规则")

    # 通知配置
    notification_enabled: bool = Field(default=True, description="是否启用通知")
    notification_channels: List[str] = Field(default=["email"], description="通知通道")
    notification_rules: List[Dict[str, Any]] = Field(default=[], description="通知规则")

    # 调度配置
    scheduler_enabled: bool = Field(default=True, description="是否启用调度")
    scheduler_interval: float = Field(default=60.0, description="调度间隔(秒)")
    scheduler_rules: List[Dict[str, Any]] = Field(default=[], description="调度规则")

    # 同步配置
    sync_enabled: bool = Field(default=True, description="是否启用同步")
    sync_interval: float = Field(default=60.0, description="同步间隔(秒)")
    sync_rules: List[Dict[str, Any]] = Field(default=[], description="同步规则")

    # 迁移配置
    migration_enabled: bool = Field(default=True, description="是否启用迁移")
    migration_interval: float = Field(default=86400.0, description="迁移间隔(秒)")
    migration_rules: List[Dict[str, Any]] = Field(default=[], description="迁移规则")

    # 维护配置
    maintenance_enabled: bool = Field(default=True, description="是否启用维护")
    maintenance_interval: float = Field(default=86400.0, description="维护间隔(秒)")
    maintenance_rules: List[Dict[str, Any]] = Field(default=[], description="维护规则")

    # 诊断配置
    diagnostic_enabled: bool = Field(default=True, description="是否启用诊断")
    diagnostic_interval: float = Field(default=300.0, description="诊断间隔(秒)")
    diagnostic_rules: List[Dict[str, Any]] = Field(default=[], description="诊断规则")

    # 优化配置
    optimization_enabled: bool = Field(default=True, description="是否启用优化")
    optimization_interval: float = Field(default=300.0, description="优化间隔(秒)")
    optimization_rules: List[Dict[str, Any]] = Field(default=[], description="优化规则")

    # 扩展配置
    extension_enabled: bool = Field(default=True, description="是否启用扩展")
    extension_path: str = Field(default="/tmp/monitor/extensions", description="扩展路径")
    extension_rules: List[Dict[str, Any]] = Field(default=[], description="扩展规则")

    # 插件配置
    plugin_enabled: bool = Field(default=True, description="是否启用插件")
    plugin_path: str = Field(default="/tmp/monitor/plugins", description="插件路径")
    plugin_rules: List[Dict[str, Any]] = Field(default=[], description="插件规则")

    # 集成配置
    integration_enabled: bool = Field(default=True, description="是否启用集成")
    integration_rules: List[Dict[str, Any]] = Field(default=[], description="集成规则")

    # 自定义配置
    custom_enabled: bool = Field(default=True, description="是否启用自定义")
    custom_rules: List[Dict[str, Any]] = Field(default=[], description="自定义规则") 