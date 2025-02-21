"""
错误码定义模块
定义所有系统使用的错误码
"""

from typing import Dict


class ErrorCodeMeta(type):
    """
    错误码元类，用于验证错误码格式
    """

    def __new__(cls, name, bases, attrs):
        # 验证错误码格式和范围
        for key, value in attrs.items():
            if isinstance(value, str) and value.isdigit():
                code = int(value)
                if not cls.is_valid_code(code):
                    raise ValueError(f"无效的错误码: {code}")
        return super().__new__(cls, name, bases, attrs)

    @staticmethod
    def is_valid_code(code: int) -> bool:
        """
        验证错误码是否有效

        Args:
            code: 错误码

        Returns:
            是否是有效的错误码
        """
        return 1000 <= code <= 9999


class ErrorCode(metaclass=ErrorCodeMeta):
    """
    错误码定义类
    """

    # 系统错误 (1000-1999)
    SYSTEM_ERROR = "1000"  # 系统内部错误
    DATABASE_ERROR = "1001"  # 数据库错误
    CACHE_ERROR = "1002"  # 缓存错误
    CONFIG_ERROR = "1003"  # 配置错误
    NETWORK_ERROR = "1004"  # 网络错误
    TASK_ERROR = "1005"  # 任务错误

    # HTTP错误 (2000-2999)
    HTTP_ERROR = "2000"  # HTTP错误
    BAD_REQUEST = "2001"  # 错误的请求
    UNAUTHORIZED = "2002"  # 未授权
    FORBIDDEN = "2003"  # 禁止访问
    NOT_FOUND = "2004"  # 资源不存在
    METHOD_NOT_ALLOWED = "2005"  # 方法不允许
    VALIDATION_ERROR = "2006"  # 验证错误
    TOO_MANY_REQUESTS = "2007"  # 请求过多

    # 业务错误 (3000-3999)
    BUSINESS_ERROR = "3000"  # 业务错误
    USER_ERROR = "3001"  # 用户相关错误
    ORDER_ERROR = "3002"  # 订单相关错误
    PAYMENT_ERROR = "3003"  # 支付相关错误
    PRODUCT_ERROR = "3004"  # 产品相关错误
    INVENTORY_ERROR = "3005"  # 库存相关错误
    PERMISSION_DENIED = "3006"  # 权限相关错误

    # 第三方服务错误 (4000-4999)
    THIRD_PARTY_ERROR = "4000"  # 第三方服务错误
    PAYMENT_SERVICE_ERROR = "4001"  # 支付服务错误
    STORAGE_SERVICE_ERROR = "4002"  # 存储服务错误
    MESSAGE_SERVICE_ERROR = "4003"  # 消息服务错误
    ANALYTICS_SERVICE_ERROR = "4004"  # 分析服务错误

    # 安全错误 (5000-5999)
    SECURITY_ERROR = "5000"  # 安全错误
    AUTHENTICATION_ERROR = "5001"  # 认证错误
    AUTHORIZATION_ERROR = "5002"  # 授权错误
    RATE_LIMIT_ERROR = "5003"  # 限流错误
    ENCRYPTION_ERROR = "5004"  # 加密错误

    # 资源错误 (6000-6999)
    RESOURCE_ERROR = "6000"  # 资源错误
    FILE_ERROR = "6001"  # 文件错误
    MEMORY_ERROR = "6002"  # 内存错误
    CPU_ERROR = "6003"  # CPU错误
    DISK_ERROR = "6004"  # 磁盘错误
    DATA_ERROR = "6005"  # 数据错误
    API_ERROR = "6006"  # API错误

    # TODO: 待整合
    # 系统级错误 (1000-1999)
    SYSTEM_ERROR = 1000  # 系统内部错误
    CONFIG_ERROR = 1001  # 配置错误
    NETWORK_ERROR = 1002  # 网络错误
    INITIALIZATION_ERROR = 1003  # 初始化错误
    SHUTDOWN_ERROR = 1004  # 关闭错误

    # 认证授权错误 (2000-2999)
    AUTH_ERROR = 2000  # 认证失败
    TOKEN_ERROR = 2001  # Token无效
    TOKEN_EXPIRED = 2002  # Token过期
    PERMISSION_ERROR = 2003  # 权限不足
    ROLE_ERROR = 2004  # 角色错误

    # 参数验证错误 (3000-3999)
    VALIDATION_ERROR = 3000  # 参数验证失败
    PARAMETER_ERROR = 3001  # 参数错误
    FORMAT_ERROR = 3002  # 格式错误
    TYPE_ERROR = 3003  # 类型错误
    RANGE_ERROR = 3004  # 范围错误

    # 数据操作错误 (4000-4999)
    DATABASE_ERROR = 4000  # 数据库错误
    CACHE_ERROR = 4001  # 缓存错误
    NOT_FOUND = 4004  # 资源不存在
    DUPLICATE_ERROR = 4005  # 重复错误
    LOCK_ERROR = 4006  # 锁错误

    # 业务逻辑错误 (5000-5999)
    BUSINESS_ERROR = 5000  # 业务逻辑错误
    STATE_ERROR = 5001  # 状态错误
    DEPENDENCY_ERROR = 5002  # 依赖错误
    CONFLICT_ERROR = 5003  # 冲突错误
    LIMIT_ERROR = 5004  # 限制错误

    # 第三方服务错误 (6000-6999)
    THIRD_PARTY_ERROR = 6000  # 第三方服务错误
    API_ERROR = 6001  # API错误
    TIMEOUT_ERROR = 6002  # 超时错误
    CONNECTION_ERROR = 6003  # 连接错误
    RESPONSE_ERROR = 6004  # 响应错误

    # 限流熔断错误 (7000-7999)
    RATE_LIMIT = 7000  # 请求限流
    CIRCUIT_BREAK = 7001  # 熔断错误
    CONCURRENCY_LIMIT = 7002  # 并发限制
    QUOTA_LIMIT = 7003  # 配额限制
    BANDWIDTH_LIMIT = 7004  # 带宽限制

    # 安全错误 (8000-8999)
    SECURITY_ERROR = 8000  # 安全错误
    CSRF_ERROR = 8001  # CSRF错误
    XSS_ERROR = 8002  # XSS错误
    INJECTION_ERROR = 8003  # 注入错误
    ENCRYPTION_ERROR = 8004  # 加密错误

    # 文件操作错误 (9000-9999)
    FILE_ERROR = 9000  # 文件错误
    UPLOAD_ERROR = 9001  # 上传错误
    DOWNLOAD_ERROR = 9002  # 下载错误
    STORAGE_ERROR = 9003  # 存储错误
    FILE_FORMAT_ERROR = 9004  # 格式错误

    @classmethod
    def get_message(cls, code: str) -> str:
        """
        获取错误码对应的默认消息

        Args:
            code: 错误码

        Returns:
            错误码对应的默认消息
        """
        for key, value in cls.__dict__.items():
            if value == code and isinstance(value, str):
                return key.lower().replace("_", " ").capitalize()
        return "未知错误"

    @classmethod
    def get_code_map(cls) -> Dict[str, str]:
        """
        获取所有错误码和消息的映射

        Returns:
            错误码和消息的映射字典
        """
        return {
            value: key.lower().replace("_", " ").capitalize()
            for key, value in cls.__dict__.items()
            if isinstance(value, str) and value.isdigit()
        }
