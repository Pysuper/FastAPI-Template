"""
角色权限相关的业务异常模块
"""

from typing import Dict, Optional

from core.exceptions.base.error_codes import ErrorCode
from core.exceptions.system.api import BusinessException


class RBACBusinessException(BusinessException):
    """角色权限业务异常基类"""

    def __init__(
        self,
        message: str,
        code: str = ErrorCode.BUSINESS_ERROR,
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        """
        初始化角色权限业务异常

        Args:
            message: 错误信息
            code: 错误码
            details: 错误详情
            context: 错误上下文
        """
        context = {"rbac_error": True, **(context or {})}
        super().__init__(message=message, code=code, details=details, context=context)


class RoleNotFoundException(RBACBusinessException):
    """角色不存在异常"""

    def __init__(
        self,
        message: str = "角色不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"role_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PermissionNotFoundException(RBACBusinessException):
    """权限不存在异常"""

    def __init__(
        self,
        message: str = "权限不存在",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"permission_not_found": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class RoleAssignmentException(RBACBusinessException):
    """角色分配异常"""

    def __init__(
        self,
        message: str = "角色分配失败",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"role_assignment_error": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class PermissionDeniedException(RBACBusinessException):
    """权限拒绝异常"""

    def __init__(
        self,
        message: str = "权限不足",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"permission_denied": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class RoleConflictException(RBACBusinessException):
    """角色冲突异常"""

    def __init__(
        self,
        message: str = "角色冲突",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"role_conflict": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)


class RoleLimitExceededException(RBACBusinessException):
    """角色数量超限异常"""

    def __init__(
        self,
        message: str = "角色数量超限",
        details: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ):
        context = {"role_limit_exceeded": True, **(context or {})}
        super().__init__(message=message, details=details, context=context)
