# from enum import Enum
#
#
# class ErrorCode(str, Enum):
#     """错误码枚举"""
#
#     # 系统级错误 (1000-1999)
#     SYSTEM_ERROR = 1000  # 系统内部错误
#     CONFIG_ERROR = 1001  # 配置错误
#     NETWORK_ERROR = 1002  # 网络错误
#     INITIALIZATION_ERROR = 1003  # 初始化错误
#     SHUTDOWN_ERROR = 1004  # 关闭错误
#
#     # 认证授权错误 (2000-2999)
#     AUTH_ERROR = 2000  # 认证失败
#     TOKEN_ERROR = 2001  # Token无效
#     TOKEN_EXPIRED = 2002  # Token过期
#     PERMISSION_ERROR = 2003  # 权限不足
#     ROLE_ERROR = 2004  # 角色错误
#
#     # 参数验证错误 (3000-3999)
#     VALIDATION_ERROR = 3000  # 参数验证失败
#     PARAMETER_ERROR = 3001  # 参数错误
#     FORMAT_ERROR = 3002  # 格式错误
#     TYPE_ERROR = 3003  # 类型错误
#     RANGE_ERROR = 3004  # 范围错误
#
#     # 数据操作错误 (4000-4999)
#     DATABASE_ERROR = 4000  # 数据库错误
#     CACHE_ERROR = 4001  # 缓存错误
#     NOT_FOUND = 4004  # 资源不存在
#     DUPLICATE_ERROR = 4005  # 重复错误
#     LOCK_ERROR = 4006  # 锁错误
#
#     # 业务逻辑错误 (5000-5999)
#     BUSINESS_ERROR = 5000  # 业务逻辑错误
#     STATE_ERROR = 5001  # 状态错误
#     DEPENDENCY_ERROR = 5002  # 依赖错误
#     CONFLICT_ERROR = 5003  # 冲突错误
#     LIMIT_ERROR = 5004  # 限制错误
#
#     # 第三方服务错误 (6000-6999)
#     THIRD_PARTY_ERROR = 6000  # 第三方服务错误
#     API_ERROR = 6001  # API错误
#     TIMEOUT_ERROR = 6002  # 超时错误
#     CONNECTION_ERROR = 6003  # 连接错误
#     RESPONSE_ERROR = 6004  # 响应错误
#
#     # 限流熔断错误 (7000-7999)
#     RATE_LIMIT = 7000  # 请求限流
#     CIRCUIT_BREAK = 7001  # 熔断错误
#     CONCURRENCY_LIMIT = 7002  # 并发限制
#     QUOTA_LIMIT = 7003  # 配额限制
#     BANDWIDTH_LIMIT = 7004  # 带宽限制
#
#     # 安全错误 (8000-8999)
#     SECURITY_ERROR = 8000  # 安全错误
#     CSRF_ERROR = 8001  # CSRF错误
#     XSS_ERROR = 8002  # XSS错误
#     INJECTION_ERROR = 8003  # 注入错误
#     ENCRYPTION_ERROR = 8004  # 加密错误
#
#     # 文件操作错误 (9000-9999)
#     FILE_ERROR = 9000  # 文件错误
#     UPLOAD_ERROR = 9001  # 上传错误
#     DOWNLOAD_ERROR = 9002  # 下载错误
#     STORAGE_ERROR = 9003  # 存储错误
#     FILE_FORMAT_ERROR = 9004  # 格式错误
