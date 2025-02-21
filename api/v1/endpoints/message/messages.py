# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：messages.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：消息管理模块

提供消息发送、接收、管理等功能
支持消息模板、消息类型和消息统计
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from core.dependencies.permissions import requires_permissions
from core.dependencies.rate_limit import rate_limiter
from fastapi import Body, Depends, Path, Query, HTTPException, status, BackgroundTasks
from services.message.message_service import MessageService
from services.notification.notification_service import NotificationService
from sqlalchemy.orm import Session

from api.base.crud import CRUDRouter
from core.cache.config.config import CacheConfig
from core.dependencies import async_db
from models.message import (
    Message,
    MessageCreate,
    MessageFilter,
    MessageUpdate,
    MessageTypeResponse,
    MessageTemplateResponse,
    MessageTemplateCreate,
    MessageTemplateUpdate,
)
from schemas.base.response import Response

# 缓存配置
MESSAGE_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "message:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 3600,  # 缓存1小时
}

router = CRUDRouter(
    model=Message,
    create_schema=MessageCreate,
    update_schema=MessageUpdate,
    filter_schema=MessageFilter,
    prefix="/messages",
    tags=["消息管理"],
    cache_config=MESSAGE_CACHE_CONFIG,
)


@router.router.get(
    "/unread",
    response_model=Response[List[Dict[str, Any]]],
    summary="获取未读消息",
    description="获取指定用户的未读消息列表",
)
@requires_permissions(["view_messages"])
async def get_unread_messages(
    user_id: int = Query(..., description="用户ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    message_type: Optional[str] = Query(None, description="消息类型"),
    db: Session = Depends(async_db),
) -> Response[List[Dict[str, Any]]]:
    """获取未读消息

    Args:
        user_id: 用户ID
        page: 页码，从1开始
        page_size: 每页记录数
        message_type: 可选的消息类型过滤
        db: 数据库会话

    Returns:
        包含未读消息列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        messages = await MessageService.get_unread_messages(
            db,
            user_id,
            skip=(page - 1) * page_size,
            limit=page_size,
            message_type=message_type,
        )
        return Response(code=200, message="获取未读消息成功", data=messages)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取未读消息失败: {str(e)}",
        )


@router.router.post(
    "/read",
    response_model=Response,
    summary="标记消息已读",
    description="将指定消息标记为已读状态",
)
@requires_permissions(["update_messages"])
async def mark_messages_read(
    message_ids: List[int] = Body(..., description="消息ID列表"),
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(async_db),
) -> Response:
    """标记消息已读

    Args:
        message_ids: 要标记的消息ID列表
        user_id: 用户ID
        db: 数据库会话

    Returns:
        标记操作的响应对象

    Raises:
        HTTPException: 标记失败时抛出
    """
    try:
        await MessageService.mark_messages_read(db, user_id, message_ids)
        return Response(code=200, message="标记消息已读成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记消息已读失败: {str(e)}",
        )


@router.router.post(
    "/send",
    response_model=Response[Dict[str, Any]],
    summary="发送消息",
    description="发送消息给指定用户",
)
@requires_permissions(["send_message"])
@rate_limiter(max_requests=10, window_seconds=60)  # 每分钟最多10次发送请求
async def send_message(
    data: MessageCreate = Body(..., description="消息数据"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """发送消息

    Args:
        data: 消息创建数据
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含发送消息信息的响应对象

    Raises:
        HTTPException: 发送失败时抛出
    """
    try:
        message = await MessageService.send_message(db, data)

        # 发送通知
        if background_tasks and data.send_notification:
            background_tasks.add_task(
                NotificationService.send_message_notification,
                message.receiver_id,
                message.title,
                message.content,
            )

        return Response(code=201, message="消息发送成功", data=message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"消息发送失败: {str(e)}")


@router.router.post(
    "/broadcast",
    response_model=Response[Dict[str, Any]],
    summary="广播消息",
    description="向所有用户或指定用户组广播消息",
)
@requires_permissions(["broadcast_message"])
@rate_limiter(max_requests=5, window_seconds=300)  # 5分钟内最多5次广播请求
async def broadcast_message(
    data: MessageCreate = Body(..., description="广播消息数据"),
    user_group: Optional[str] = Query(None, description="用户组"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """广播消息

    Args:
        data: 广播消息数据
        user_group: 可选的用户组过滤
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        包含广播消息信息的响应对象

    Raises:
        HTTPException: 广播失败时抛出
    """
    try:
        message = await MessageService.broadcast_message(db, data, user_group=user_group)

        # 发送通知
        if background_tasks and data.send_notification:
            background_tasks.add_task(
                NotificationService.send_broadcast_notification, message.title, message.content, user_group
            )

        return Response(code=201, message="消息广播成功", data=message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"消息广播失败: {str(e)}")


@router.router.get(
    "/types",
    response_model=Response[List[MessageTypeResponse]],
    summary="获取消息类型列表",
    description="获取所有可用的消息类型列表",
)
@requires_permissions(["view_message_types"])
async def get_message_types(db: Session = Depends(async_db)) -> Response[List[MessageTypeResponse]]:
    """获取消息类型列表

    Args:
        db: 数据库会话

    Returns:
        包含消息类型列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        types = await MessageService.get_message_types(db)
        return Response(code=200, message="获取消息类型列表成功", data=types)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取消息类型列表失败: {str(e)}")


@router.router.get(
    "/templates",
    response_model=Response[List[MessageTemplateResponse]],
    summary="获取消息模板列表",
    description="获取所有可用的消息模板列表",
)
@requires_permissions(["view_message_templates"])
async def get_message_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    template_type: Optional[str] = Query(None, description="模板类型"),
    db: Session = Depends(async_db),
) -> Response[List[MessageTemplateResponse]]:
    """获取消息模板列表

    Args:
        page: 页码，从1开始
        page_size: 每页记录数
        template_type: 可选的模板类型过滤
        db: 数据库会话

    Returns:
        包含消息模板列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        templates = await MessageService.get_message_templates(
            db,
            skip=(page - 1) * page_size,
            limit=page_size,
            template_type=template_type,
        )
        return Response(code=200, message="获取消息模板列表成功", data=templates)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取消息模板列表失败: {str(e)}",
        )


@router.router.post(
    "/templates",
    response_model=Response[MessageTemplateResponse],
    summary="创建消息模板",
    description="创建新的消息模板",
)
@requires_permissions(["create_message_template"])
async def create_message_template(
    data: MessageTemplateCreate = Body(..., description="消息模板创建数据"),
    db: Session = Depends(async_db),
) -> Response[MessageTemplateResponse]:
    """创建消息模板

    Args:
        data: 消息模板创建数据
        db: 数据库会话

    Returns:
        包含新创建的消息模板的响应对象

    Raises:
        HTTPException: 创建失败时抛出
    """
    try:
        template = await MessageService.create_message_template(db, data)
        return Response(code=201, message="创建消息模板成功", data=template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建消息模板失败: {str(e)}",
        )


@router.router.put(
    "/templates/{template_id}",
    response_model=Response[MessageTemplateResponse],
    summary="更新消息模板",
    description="更新指定的消息模板",
)
@requires_permissions(["update_message_template"])
async def update_message_template(
    template_id: int = Path(..., description="消息模板ID"),
    data: MessageTemplateUpdate = Body(..., description="消息模板更新数据"),
    db: Session = Depends(async_db),
) -> Response[MessageTemplateResponse]:
    """更新消息模板

    Args:
        template_id: 消息模板ID
        data: 消息模板更新数据
        db: 数据库会话

    Returns:
        包含更新后的消息模板的响应对象

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        template = await MessageService.update_message_template(db, template_id, data)
        return Response(code=200, message="更新消息模板成功", data=template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新消息模板失败: {str(e)}",
        )


@router.router.delete(
    "/templates/{template_id}",
    response_model=Response,
    summary="删除消息模板",
    description="删除指定的消息模板",
)
@requires_permissions(["delete_message_template"])
async def delete_message_template(
    template_id: int = Path(..., description="消息模板ID"),
    db: Session = Depends(async_db),
) -> Response:
    """删除消息模板

    Args:
        template_id: 消息模板ID
        db: 数据库会话

    Returns:
        删除操作的响应对象

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        await MessageService.delete_message_template(db, template_id)
        return Response(code=200, message="删除消息模板成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除消息模板失败: {str(e)}",
        )


@router.router.get(
    "/stats",
    response_model=Response[Dict[str, Any]],
    summary="获取消息统计",
    description="获取指定用户的消息统计信息",
)
@requires_permissions(["view_message_stats"])
async def get_message_stats(
    user_id: int = Query(..., description="用户ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(async_db),
) -> Response[Dict[str, Any]]:
    """获取消息统计

    Args:
        user_id: 用户ID
        start_date: 可选的开始日期
        end_date: 可选的结束日期
        db: 数据库会话

    Returns:
        包含消息统计信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        stats = await MessageService.get_message_stats(
            db,
            user_id,
            start_date=start_date,
            end_date=end_date,
        )
        return Response(code=200, message="获取消息统计成功", data=stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取消息统计失败: {str(e)}",
        )


# 新增API端点
@router.router.post(
    "/batch-delete",
    response_model=Response,
    summary="批量删除消息",
    description="批量删除指定的消息",
)
@requires_permissions(["delete_messages"])
async def batch_delete_messages(
    message_ids: List[int] = Body(..., description="消息ID列表"),
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(async_db),
) -> Response:
    """批量删除消息

    Args:
        message_ids: 要删除的消息ID列表
        user_id: 用户ID
        db: 数据库会话

    Returns:
        删除操作的响应对象

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        await MessageService.batch_delete_messages(db, user_id, message_ids)
        return Response(code=200, message="批量删除消息成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除消息失败: {str(e)}",
        )


@router.router.post(
    "/mark-all-read",
    response_model=Response,
    summary="标记所有消息已读",
    description="将用户的所有未读消息标记为已读",
)
@requires_permissions(["update_messages"])
async def mark_all_messages_read(
    user_id: int = Query(..., description="用户ID"),
    message_type: Optional[str] = Query(None, description="消息类型"),
    db: Session = Depends(async_db),
) -> Response:
    """标记所有消息已读

    Args:
        user_id: 用户ID
        message_type: 可选的消息类型过滤
        db: 数据库会话

    Returns:
        标记操作的响应对象

    Raises:
        HTTPException: 标记失败时抛出
    """
    try:
        await MessageService.mark_all_messages_read(db, user_id, message_type=message_type)
        return Response(code=200, message="标记所有消息已读成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"标记所有消息已读失败: {str(e)}")
