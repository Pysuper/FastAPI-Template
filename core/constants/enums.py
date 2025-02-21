from enum import Enum, IntEnum


class UserStatus(IntEnum):
    """
    用户状态
    """

    INACTIVE = 0  # 未激活
    ACTIVE = 1  # 正常
    DISABLED = 2  # 禁用
    DELETED = 3  # 已删除


class UserRole(str, Enum):
    """
    用户角色
    """

    ADMIN = "admin"  # 管理员
    OPERATOR = "operator"  # 运营
    USER = "user"  # 普通用户


class FileType(str, Enum):
    """
    文件类型
    """

    IMAGE = "image"  # 图片
    VIDEO = "video"  # 视频
    AUDIO = "audio"  # 音频
    DOC = "doc"  # 文档
    OTHER = "other"  # 其他


class CacheType(str, Enum):
    """
    缓存类型
    """

    REDIS = "redis"  # Redis缓存
    LOCAL = "local"  # 本地缓存
    NONE = "none"  # 不使用缓存


class LogLevel(str, Enum):
    """
    日志级别
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# 状态码常量
class StatusCode:
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500


# 错误消息常量
class ErrorMessages:
    INVALID_CREDENTIALS = "Invalid credentials"
    PERMISSION_DENIED = "Permission denied"
    RESOURCE_NOT_FOUND = "Resource not found"
    VALIDATION_ERROR = "Validation error"
    INTERNAL_SERVER_ERROR = "Internal server error"


class ResourceType(str, Enum):
    STUDENT = "student"
    COURSE = "course"
    LIBRARY = "library"
    EXAM = "exam"
    PARENT = "parent"
    ACTIVITY = "activity"


class Action(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"
