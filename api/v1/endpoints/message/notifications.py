# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：notifications.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：通知管理模块

提供通知发送、接收、管理等功能
支持通知模板、通知类型和通知统计
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from core.dependencies.permissions import requires_permissions
from core.dependencies.rate_limit import rate_limiter
from fastapi import Body, Depends, Path, Query, HTTPException, status, BackgroundTasks
from services.notification.notification_service import NotificationService
from sqlalchemy.orm import Session

from api.base.crud import CRUDRouter
from core.cache.config.config import CacheConfig
from core.dependencies import async_db
from models.parent import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationFilter,
    NotificationTypeResponse,
    NotificationTemplateResponse,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
)
from schemas.base.response import Response

# 缓存配置
NOTIFICATION_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "notification:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 3600,  # 缓存1小时
}

router = CRUDRouter(
    model=Notification,
    create_schema=NotificationCreate,
    update_schema=NotificationUpdate,
    filter_schema=NotificationFilter,
    prefix="/notifications",
    tags=["通知管理"],
    cache_config=NOTIFICATION_CACHE_CONFIG,
)


@router.router.get(
    "/unread",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取未读通知",
    description="获取指定用户的未读通知列表",
)
@requires_permissions(["view_notifications"])
async def get_unread_notifications(
    user_id: int = Query(..., description="用户ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    notification_type: Optional[str] = Query(None, description="通知类型"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取未读通知

    Args:
        user_id: 用户ID
        page: 页码，从1开始
        page_size: 每页记录数
        notification_type: 可选的通知类型过滤
        db: 数据库会话

    Returns:
        包含未读通知列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        notifications = await NotificationService.get_unread_notifications(
            db,
            user_id,
            skip=(page - 1) * page_size,
            limit=page_size,
            notification_type=notification_type,
        )
        return Response(code=200, message="获取未读通知成功", data=notifications)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取未读通知失败: {str(e)}",
        )


j


@router.router.post(
    "/read",
    response_model=Response,
    summary="标记通知已读",
    description="将指定通知标记为已读状态",
)
@requires_permissions(["update_notifications"])
async def mark_notifications_read(
    notification_ids: List[int] = Body(..., description="通知ID列表"),
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(async_db),
) -> Response:
    """标记通知已读

    Args:
        notification_ids: 要标记的通知ID列表
        user_id: 用户ID
        db: 数据库会话

    Returns:
        标记操作的响应对象

    Raises:
        HTTPException: 标记失败时抛出
    """
    try:
        await NotificationService.mark_notifications_read(db, user_id, notification_ids)
        return Response(code=200, message="标记通知已读成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记通知已读失败: {str(e)}",
        )


@router.router.post(
    "/send",
    response_model=Response[Dict[str, Any]],
    summary="发送通知",
    description="发送通知给指定用户",
)
@requires_permissions(["send_notification"])
@rate_limiter(max_requests=10, window_seconds=60)  # 每分钟最多10次发送请求
async def send_notification(
    data: NotificationCreate = Body(..., description="通知数据"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """发送通知

    Args:
        data: 通知创建数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含发送通知信息的响应对象

    Raises:
        HTTPException: 发送失败时抛出
    """
    try:
        notification = await NotificationService.send_notification(db, data)

        # 发送推送通知
        if background_tasks and data.send_push:
            background_tasks.add_task(
                NotificationService.send_push_notification,
                notification.receiver_id,
                notification.title,
                notification.content,
            )

        return Response(code=201, message="通知发送成功", data=notification)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"通知发送失败: {str(e)}",
        )


@router.router.post(
    "/broadcast",
    response_model=Response[Dict[str, Any]],
    summary="广播通知",
    description="向所有用户或指定用户组广播通知",
)
@requires_permissions(["broadcast_notification"])
@rate_limiter(max_requests=5, window_seconds=300)  # 5分钟内最多5次广播请求
async def broadcast_notification(
    data: NotificationCreate = Body(..., description="广播通知数据"),
    user_group: Optional[str] = Query(None, description="用户组"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """广播通知

    Args:
        data: 广播通知数据
        user_group: 可选的用户组过滤
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含广播通知信息的响应对象

    Raises:
        HTTPException: 广播失败时抛出
    """
    try:
        notification = await NotificationService.broadcast_notification(db, data, user_group=user_group)

        # 发送推送通知
        if background_tasks and data.send_push:
            background_tasks.add_task(
                NotificationService.send_broadcast_push,
                notification.title,
                notification.content,
                user_group,
            )

        return Response(code=201, message="通知广播成功", data=notification)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"通知广播失败: {str(e)}",
        )


@router.router.get(
    "/types",
    response_model=Response[List[NotificationTypeResponse]],
    summary="获取通知类型列表",
    description="获取所有可用的通知类型列表",
)
@requires_permissions(["view_notification_types"])
async def get_notification_types(db: Session = Depends(async_db)) -> Response[List[NotificationTypeResponse]]:
    """获取通知类型列表

    Args:
        db: 数据库会话

    Returns:
        包含通知类型列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        types = await NotificationService.get_notification_types(db)
        return Response(code=200, message="获取通知类型列表成功", data=types)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知类型列表失败: {str(e)}",
        )


@router.router.get(
    "/templates",
    response_model=Response[List[NotificationTemplateResponse]],
    summary="获取通知模板列表",
    description="获取所有可用的通知模板列表",
)
@requires_permissions(["view_notification_templates"])
async def get_notification_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    template_type: Optional[str] = Query(None, description="模板类型"),
    db: Session = Depends(async_db),
) -> Response[List[NotificationTemplateResponse]]:
    """获取通知模板列表

    Args:
        page: 页码，从1开始
        page_size: 每页记录数
        template_type: 可选的模板类型过滤
        db: 数据库会话

    Returns:
        包含通知模板列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        templates = await NotificationService.get_notification_templates(
            db, skip=(page - 1) * page_size, limit=page_size, template_type=template_type
        )
        return Response(code=200, message="获取通知模板列表成功", data=templates)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知模板列表失败: {str(e)}",
        )


@router.router.post(
    "/templates",
    response_model=Response[NotificationTemplateResponse],
    summary="创建通知模板",
    description="创建新的通知模板",
)
@requires_permissions(["create_notification_template"])
async def create_notification_template(
    data: NotificationTemplateCreate = Body(..., description="通知模板创建数据"),
    db: Session = Depends(async_db),
) -> Response[NotificationTemplateResponse]:
    """创建通知模板

    Args:
        data: 通知模板创建数据
        db: 数据库会话

    Returns:
        包含新创建的通知模板的响应对象

    Raises:
        HTTPException: 创建失败时抛出
    """
    try:
        template = await NotificationService.create_notification_template(db, data)
        return Response(code=201, message="创建通知模板成功", data=template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建通知模板失败: {str(e)}",
        )


@router.router.put(
    "/templates/{template_id}",
    response_model=Response[NotificationTemplateResponse],
    summary="更新通知模板",
    description="更新指定的通知模板",
)
@requires_permissions(["update_notification_template"])
async def update_notification_template(
    template_id: int = Path(..., description="通知模板ID"),
    data: NotificationTemplateUpdate = Body(..., description="通知模板更新数据"),
    db: Session = Depends(async_db),
) -> Response[NotificationTemplateResponse]:
    """更新通知模板

    Args:
        template_id: 通知模板ID
        data: 通知模板更新数据
        db: 数据库会话

    Returns:
        包含更新后的通知模板的响应对象

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        template = await NotificationService.update_notification_template(db, template_id, data)
        return Response(code=200, message="更新通知模板成功", data=template)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新通知模板失败: {str(e)}")


@router.router.delete(
    "/templates/{template_id}",
    response_model=Response,
    summary="删除通知模板",
    description="删除指定的通知模板",
)
@requires_permissions(["delete_notification_template"])
async def delete_notification_template(
    template_id: int = Path(..., description="通知模板ID"),
    db: Session = Depends(async_db),
) -> Response:
    """删除通知模板

    Args:
        template_id: 通知模板ID
        db: 数据库会话

    Returns:
        删除操作的响应对象

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        await NotificationService.delete_notification_template(db, template_id)
        return Response(code=200, message="删除通知模板成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除通知模板失败: {str(e)}",
        )


@router.router.get(
    "/stats",
    response_model=Response[Dict[str, Any]],
    summary="获取通知统计",
    description="获取指定用户的通知统计信息",
)
@requires_permissions(["view_notification_stats"])
async def get_notification_stats(
    user_id: int = Query(..., description="用户ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取通知统计

    Args:
        user_id: 用户ID
        start_date: 可选的开始日期
        end_date: 可选的结束日期
        db: 数据库会话

    Returns:
        包含通知统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await NotificationService.get_notification_stats(
            db,
            user_id,
            start_date=start_date,
            end_date=end_date,
        )
        return Response(code=200, message="获取通知统计成功", data=stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知统计失败: {str(e)}",
        )


# 新增API端点
@router.router.post(
    "/batch-delete",
    response_model=Response,
    summary="批量删除通知",
    description="批量删除指定的通知",
)
@requires_permissions(["delete_notifications"])
async def batch_delete_notifications(
    notification_ids: List[int] = Body(..., description="通知ID列表"),
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(async_db),
) -> Response:
    """批量删除通知

    Args:
        notification_ids: 要删除的通知ID列表
        user_id: 用户ID
        db: 数据库会话

    Returns:
        删除操作的响应对象

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        await NotificationService.batch_delete_notifications(db, user_id, notification_ids)
        return Response(code=200, message="批量删除通知成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量删除通知失败: {str(e)}")


@router.router.post(
    "/mark-all-read",
    response_model=Response,
    summary="标记所有通知已读",
    description="将用户的所有未读通知标记为已读",
)
@requires_permissions(["update_notifications"])
async def mark_all_notifications_read(
    user_id: int = Query(..., description="用户ID"),
    notification_type: Optional[str] = Query(None, description="通知类型"),
    db: Session = Depends(async_db),
) -> Response:
    """标记所有通知已读

    Args:
        user_id: 用户ID
        notification_type: 可选的通知类型过滤
        db: 数据库会话

    Returns:
        标记操作的响应对象

    Raises:
        HTTPException: 标记失败时抛出
    """
    try:
        await NotificationService.mark_all_notifications_read(db, user_id, notification_type=notification_type)
        return Response(code=200, message="标记所有通知已读成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"标记所有通知已读失败: {str(e)}")


@router.router.post("/subscribe", response_model=Response, summary="订阅通知", description="订阅指定类型的通知")
@requires_permissions(["subscribe_notifications"])
async def subscribe_notifications(
    user_id: int = Query(..., description="用户ID"),
    notification_types: List[str] = Body(..., description="通知类型列表"),
    db: Session = Depends(async_db),
) -> Response:
    """订阅通知

    Args:
        user_id: 用户ID
        notification_types: 要订阅的通知类型列表
        db: 数据库会话

    Returns:
        订阅操作的响应对象

    Raises:
        HTTPException: 订阅失败时抛出
    """
    try:
        await NotificationService.subscribe_notifications(db, user_id, notification_types)
        return Response(code=200, message="通知订阅成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"通知订阅失败: {str(e)}")


@router.router.post(
    "/unsubscribe", response_model=Response, summary="取消订阅通知", description="取消订阅指定类型的通知"
)
@requires_permissions(["unsubscribe_notifications"])
async def unsubscribe_notifications(
    user_id: int = Query(..., description="用户ID"),
    notification_types: List[str] = Body(..., description="通知类型列表"),
    db: Session = Depends(async_db),
) -> Response:
    """取消订阅通知

    Args:
        user_id: 用户ID
        notification_types: 要取消订阅的通知类型列表
        db: 数据库会话

    Returns:
        取消订阅操作的响应对象

    Raises:
        HTTPException: 取消订阅失败时抛出
    """
    try:
        await NotificationService.unsubscribe_notifications(db, user_id, notification_types)
        return Response(code=200, message="取消通知订阅成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消通知订阅失败: {str(e)}",
        )


@router.router.get(
    "/subscriptions",
    response_model=Response[List[str]],
    summary="获取通知订阅",
    description="获取用户的通知订阅列表",
)
@requires_permissions(["view_notification_subscriptions"])
async def get_notification_subscriptions(
    user_id: int = Query(..., description="用户ID"), db: Session = Depends(async_db)
) -> Response[List[str]]:
    """获取通知订阅

    Args:
        user_id: 用户ID
        db: 数据库会话

    Returns:
        包含用户订阅的通知类型列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        subscriptions = await NotificationService.get_notification_subscriptions(db, user_id)
        return Response(code=200, message="获取通知订阅列表成功", data=subscriptions)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知订阅列表失败: {str(e)}",
        )
