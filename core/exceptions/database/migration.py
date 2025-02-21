"""
数据库迁移相关的异常模块
"""
from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class MigrationException(BusinessException):
    """迁移异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.DATABASE_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化迁移异常
        
        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"migration_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class MigrationVersionException(MigrationException):
    """迁移版本异常"""

    def __init__(
        self,
        message: str = "迁移版本错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"version_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MigrationDependencyException(MigrationException):
    """迁移依赖异常"""

    def __init__(
        self,
        message: str = "迁移依赖错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"dependency_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MigrationConflictException(MigrationException):
    """迁移冲突异常"""

    def __init__(
        self,
        message: str = "迁移冲突",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"conflict_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MigrationRollbackException(MigrationException):
    """迁移回滚异常"""

    def __init__(
        self,
        message: str = "迁移回滚失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"rollback_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MigrationSchemaException(MigrationException):
    """迁移架构异常"""

    def __init__(
        self,
        message: str = "数据库架构错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"schema_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class MigrationDataException(MigrationException):
    """迁移数据异常"""

    def __init__(
        self,
        message: str = "数据迁移错误",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"data_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context) 