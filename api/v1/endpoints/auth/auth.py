# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：auth.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：认证管理模块

提供用户认证、注册、登录、密码管理等功能
支持多种认证方式、安全控制和数据验证
"""
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from constants.users import TokenType
from core.cache.config.config import CacheConfig
from core.decorators.cache import rate_limit
from core.dependencies import async_db
from core.dependencies.auth import get_current_active_user
from core.loge.manager import logic
from exceptions.http.auth import AuthenticationException
from models.user import User, UserStatus
from schemas.base.response import Response
from schemas.validators.rbac import (
    UserCreate,
    UserEmailVerify,
    UserLogin,
    UserPasswordReset,
    UserPhoneVerify,
    UserUpdate,
)
from schemas.validators.token import TokenPayload, TokenResponse
from services.auth.email import EmailService
from services.auth.sms import SMSService
from utils.security import (
    create_access_token,
    create_refresh_token,
    generate_verification_code,
    get_password_hash,
    verify_password,
)

# 缓存配置
AUTH_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "auth:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 3600,  # 缓存1小时
}

router = APIRouter()


@router.post(
    "/register",
    response_model=Response[TokenResponse],
    summary="用户注册",
    description="注册新用户并返回访问令牌",
)
@rate_limit("register", 30, 300, scope="auth")  # 5次/5分钟
async def register(
    data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(async_db),
) -> Response[TokenResponse]:
    """注册新用户

    Args:
        data: 用户注册数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含访问令牌的响应对象

    Raises:
        AuthenticationException: 注册失败时抛出
    """
    try:
        # 检查用户名是否已存在
        result = await db.execute(select(User).filter(User.username == data.username))
        if result.unique().scalar_one_or_none():
            raise AuthenticationException("用户名已存在")

        # 检查邮箱是否已存在
        result = await db.execute(select(User).filter(User.email == data.email))
        if result.unique().scalar_one_or_none():
            raise AuthenticationException("邮箱已存在")

        # 创建新用户
        user = User(
            username=data.username,
            email=data.email,
            password=get_password_hash(data.password),
            full_name=data.full_name,
            is_active=True,
            is_superuser=False,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # 生成令牌
        access_token = await create_access_token({"sub": str(user.id)})
        refresh_token = await create_refresh_token({"sub": str(user.id)})

        # 发送欢迎邮件
        background_tasks.add_task(EmailService.send_welcome_email, user.email, user.full_name)

        return Response(
            code="201",
            message="注册成功",
            data={
                "user_id": user.id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,  # 令牌有效期1小时
            },
        )
    except Exception as e:
        await db.rollback()
        raise AuthenticationException(f"注册失败: {str(e)}")


@router.post(
    "/login",
    response_model=Response[TokenResponse],
    summary="用户登录",
    description="使用用户名和密码登录",
)
@rate_limit("login", 30, 300, scope="auth")  # 30次/5分钟
async def login(
    data: UserLogin,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(async_db),
) -> Response[TokenResponse]:
    """用户登录

    Args:
        data: 登录数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含访问令牌的响应对象

    Raises:
        AuthenticationException: 登录失败时抛出
    """
    try:
        # 查找用户
        result = await db.execute(select(User).filter(User.username == data.username))
        user = result.unique().scalar_one_or_none()
        if not user:
            raise AuthenticationException("用户名或密码错误")

        # 验证密码
        if not verify_password(data.password, user.password):
            # 更新登录失败次数
            user.failed_login_count += 1
            if user.failed_login_count >= 5:  # 5次失败后锁定账户
                user.status = UserStatus.LOCKED
                user.locked_until = datetime.now() + timedelta(minutes=30)  # 锁定30分钟
            await db.commit()
            raise AuthenticationException("用户名或密码错误")

        # 检查用户状态
        if user.status == UserStatus.LOCKED:
            if user.locked_until and user.locked_until > datetime.now():
                raise AuthenticationException(f"账户已锁定，请在{user.locked_until}后重试")
            user.status = UserStatus.ACTIVE
            user.locked_until = None

        # 更新用户信息
        user.last_login = datetime.now()
        user.last_active = datetime.now()
        user.failed_login_count = 0
        user.login_count += 1
        await db.commit()

        # 生成令牌
        access_token = await create_access_token({"sub": str(user.id)})
        refresh_token = await create_refresh_token({"sub": str(user.id)})

        # 尝试发送登录通知，但不影响登录流程
        try:
            if user.phone:  # 只在用户设置了手机号时尝试发送
                background_tasks.add_task(
                    SMSService.send_login_notification,
                    user.phone,
                    "未知地点",  # TODO: 获取实际登录地点
                    "未知设备",  # TODO: 获取实际登录设备
                    user.last_login.strftime("%Y-%m-%d %H:%M:%S"),
                )
        except Exception as e:
            # 记录错误但不影响登录流程
            logic.error(f"发送登录通知失败: {str(e)}")

        return Response(
            code="200",
            message="登录成功",
            data={
                "user_id": user.id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,  # 令牌有效期1小时
            },
        )
    except Exception as e:
        await db.rollback()
        raise AuthenticationException(f"登录失败: {str(e)}")


@router.post(
    "/logout",
    response_model=Response,
    summary="用户登出",
    description="注销当前用户的登录状态",
)
async def logout(current_user: User = Depends(get_current_active_user)) -> Response:
    """用户登出

    Args:
        current_user: 当前登录用户

    Returns:
        成功响应
    """
    # TODO: 实现令牌黑名单
    return Response(code=200, message="登出成功")


@router.post(
    "/refresh-token",
    response_model=Response[TokenResponse],
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌",
)
@rate_limit("refresh_token", 50, 300, scope="auth")  # 5次/5分钟
async def refresh_token(refresh_token: str = Body(..., embed=True)) -> Response[TokenResponse]:
    """刷新访问令牌

    Args:
        refresh_token: 刷新令牌

    Returns:
        包含新访问令牌的响应对象

    Raises:
        AuthenticationException: 刷新失败时抛出
    """
    try:
        # 验证刷新令牌
        payload = TokenPayload.validate_refresh_token(refresh_token)
        if not payload:
            raise AuthenticationException("无效的刷新令牌")

        # 生成新的访问令牌
        access_token = await create_access_token({"sub": payload.sub})
        new_refresh_token = await create_refresh_token({"sub": payload.sub})

        return Response(
            code=200,
            message="令牌刷新成功",
            data={
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,  # 令牌有效期1小时
            },
        )
    except Exception as e:
        raise AuthenticationException(f"令牌刷新失败: {str(e)}")


@router.post(
    "/forgot-password",
    response_model=Response,
    summary="忘记密码",
    description="发送密码重置邮件",
)
@rate_limit("forgot_password", 30, 1800, scope="auth")  # 3次/30分钟
async def forgot_password(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(async_db),
    email: str = Body(..., embed=True),
) -> Response:
    """发送密码重置邮件

    Args:
        background_tasks: 后台任务
        db: 数据库会话
        email: 用户邮箱

    Returns:
        成功响应

    Raises:
        AuthenticationException: 发送失败时抛出
    """
    try:
        # 查找用户
        result = await db.execute(select(User).filter(User.email == email))
        user = result.unique().scalar_one_or_none()
        if not user:
            # 即使用户不存在也返回成功，避免泄露用户信息
            return Response(code=200, message="如果邮箱存在，重置密码邮件将发送到该邮箱")

        # 生成重置令牌
        reset_token = await create_access_token(
            {"sub": str(user.id), "type": TokenType.RESET_PASSWORD},
            expires_delta=timedelta(minutes=30),  # 30分钟有效期
        )

        # 发送重置密码邮件
        background_tasks.add_task(
            EmailService.send_password_reset_email,
            user.email,
            user.full_name,
            reset_token,
        )

        return Response(code=200, message="如果邮箱存在，重置密码邮件将发送到该邮箱")
    except Exception as e:
        raise AuthenticationException(f"发送重置密码邮件失败: {str(e)}")


@router.post(
    "/reset-password",
    response_model=Response,
    summary="重置密码",
    description="使用重置令牌重置密码",
)
@rate_limit("reset_password", 30, 1800, scope="auth")  # 3次/30分钟
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(async_db),
) -> Response:
    """重置密码

    Args:
        token: 重置令牌
        new_password: 新密码
        db: 数据库会话

    Returns:
        成功响应

    Raises:
        AuthenticationException: 重置失败时抛出
    """
    try:
        # 验证重置令牌
        payload = TokenPayload.validate_access_token(token)
        if not payload or payload.type != "reset_password":
            raise AuthenticationException("无效的重置令牌")

        # 查找用户
        result = await db.execute(select(User).filter(User.id == int(payload.sub)))
        user = result.unique().scalar_one_or_none()
        if not user:
            raise AuthenticationException("用户不存在")

        # 更新密码
        user.password = get_password_hash(new_password)
        user.password_changed_at = datetime.now()
        user.updated_at = datetime.now()
        await db.commit()

        return Response(code=200, message="密码重置成功")
    except Exception as e:
        await db.rollback()
        raise AuthenticationException(f"密码重置失败: {str(e)}")


@router.post(
    "/change-password",
    response_model=Response,
    summary="修改密码",
    description="修改当前用户的密码",
)
@rate_limit("change_password", 30, 1800, scope="auth")  # 3次/30分钟
async def change_password(
    data: UserPasswordReset,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(async_db),
) -> Response:
    """修改密码

    Args:
        data: 密码修改数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        成功响应

    Raises:
        AuthenticationException: 修改失败时抛出
    """
    try:
        # 验证旧密码
        if not verify_password(data.old_password, current_user.password):
            raise AuthenticationException("旧密码错误")

        # 更新密码
        current_user.password = get_password_hash(data.new_password)
        current_user.password_changed_at = datetime.now()
        current_user.updated_at = datetime.now()
        await db.commit()

        return Response(code=200, message="密码修改成功")
    except Exception as e:
        await db.rollback()
        raise AuthenticationException(f"密码修改失败: {str(e)}")


@router.post(
    "/send-email-code",
    response_model=Response,
    summary="发送邮箱验证码",
    description="发送邮箱验证码",
)
@rate_limit("send_email_code", 10, 60, scope="auth")  # 1次/分钟
async def send_email_code(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(async_db),
    email: str = Body(..., embed=True),
) -> Response:
    """发送邮箱验证码

    Args:
        background_tasks: 后台任务
        db: 数据库会话
        email: 邮箱地址

    Returns:
        成功响应

    Raises:
        AuthenticationException: 发送失败时抛出
    """
    try:
        # 查找用户
        result = await db.execute(select(User).filter(User.email == email))
        user = result.unique().scalar_one_or_none()
        if not user:
            raise AuthenticationException("用户不存在")

        # 生成验证码
        code = generate_verification_code()

        # 发送验证码邮件
        background_tasks.add_task(EmailService.send_verification_code_email, user.email, user.full_name, code)

        # TODO: 保存验证码到缓存

        return Response(code=200, message="验证码已发送")
    except Exception as e:
        raise AuthenticationException(f"发送验证码失败: {str(e)}")


@router.post(
    "/verify-email",
    response_model=Response,
    summary="验证邮箱",
    description="验证邮箱",
)
@rate_limit("verify_email", 50, 300, scope="auth")  # 5次/5分钟
async def verify_email(
    data: UserEmailVerify,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(async_db),
) -> Response:
    """验证邮箱

    Args:
        data: 邮箱验证数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        成功响应

    Raises:
        AuthenticationException: 验证失败时抛出
    """
    try:
        # TODO: 从缓存获取验证码
        code = "123456"  # 临时代码

        # 验证验证码
        if data.code != code:
            raise AuthenticationException("验证码错误")

        # 更新用户信息
        current_user.is_verified = True
        current_user.updated_at = datetime.now()
        await db.commit()

        return Response(code=200, message="邮箱验证成功")
    except Exception as e:
        await db.rollback()
        raise AuthenticationException(f"邮箱验证失败: {str(e)}")


@router.post(
    "/send-sms-code",
    response_model=Response,
    summary="发送短信验证码",
    description="发送短信验证码",
)
@rate_limit("send_sms_code", 10, 60, scope="auth")  # 1次/分钟
async def send_sms_code(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(async_db),
    phone: str = Body(..., embed=True),
) -> Response:
    """发送短信验证码

    Args:
        background_tasks: 后台任务
        db: 数据库会话
        phone: 手机号码

    Returns:
        成功响应

    Raises:
        AuthenticationException: 发送失败时抛出
    """
    try:
        # 查找用户
        result = await db.execute(select(User).filter(User.phone == phone))
        user = result.unique().scalar_one_or_none()
        if not user:
            raise AuthenticationException("用户不存在")

        # 生成验证码
        code = generate_verification_code()

        # 发送验证码短信
        background_tasks.add_task(SMSService.send_verification_code_sms, user.phone, code)

        # TODO: 保存验证码到缓存

        return Response(code=200, message="验证码已发送")
    except Exception as e:
        raise AuthenticationException(f"发送验证码失败: {str(e)}")


@router.post(
    "/verify-phone",
    response_model=Response,
    summary="验证手机",
    description="验证手机",
)
@rate_limit("verify_phone", 50, 300, scope="auth")  # 5次/5分钟
async def verify_phone(
    data: UserPhoneVerify,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(async_db),
) -> Response:
    """验证手机

    Args:
        data: 手机验证数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        成功响应

    Raises:
        AuthenticationException: 验证失败时抛出
    """
    try:
        # TODO: 从缓存获取验证码
        code = "123456"  # 临时代码

        # 验证验证码
        if data.code != code:
            raise AuthenticationException("验证码错误")

        # 更新用户信息
        current_user.is_verified = True
        current_user.updated_at = datetime.now()
        await db.commit()

        return Response(code=200, message="手机验证成功")
    except Exception as e:
        await db.rollback()
        raise AuthenticationException(f"手机验证失败: {str(e)}")


@router.get(
    "/me",
    response_model=Response[Dict[str, Any]],
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
)
async def get_current_user(current_user: User = Depends(get_current_active_user)) -> Response[Dict[str, Any]]:
    """获取当前用户信息

    Args:
        current_user: 当前登录用户

    Returns:
        包含用户信息的响应对象
    """
    return Response(
        code=200,
        message="获取成功",
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "is_superuser": current_user.is_superuser,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
        },
    )


@router.put(
    "/me",
    response_model=Response[Dict[str, Any]],
    summary="更新当前用户信息",
    description="更新当前登录用户的信息",
)
async def update_current_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """更新当前用户信息

    Args:
        data: 用户更新数据
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        包含更新后用户信息的响应对象

    Raises:
        AuthenticationException: 更新失败时抛出
    """
    try:
        # 更新用户信息
        for field, value in data.dict(exclude_unset=True).items():
            setattr(current_user, field, value)
        current_user.updated_at = datetime.now()
        await db.commit()
        await db.refresh(current_user)

        return Response(
            code=200,
            message="更新成功",
            data={
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "is_active": current_user.is_active,
                "is_superuser": current_user.is_superuser,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at,
            },
        )
    except Exception as e:
        await db.rollback()
        raise AuthenticationException(f"更新失败: {str(e)}")
