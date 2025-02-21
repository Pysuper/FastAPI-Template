from typing import Optional

from core.auth.permissions import Action, PermissionChecker, ResourceType
from core.db.database import get_db
from core.logger import logger
from core.validators import ActivityCreate, ActivityUpdate, ResponseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.cache import Cache
from services.activity import ActivityService

router = APIRouter(prefix="/activities", tags=["activities"])
permission = PermissionChecker(get_db(), Cache())


@router.get("", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.READ)
async def get_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    type: Optional[str] = None,
    is_public: Optional[bool] = None,
    organizer_id: Optional[int] = None,
    db: Session = Depends(async_db),
):
    """获取活动列表"""
    try:
        service = ActivityService(db, Cache())
        activities = await service.get_activities(
            skip=skip, limit=limit, type=type, is_public=is_public, organizer_id=organizer_id
        )
        return ResponseModel(data={"activities": [a.__dict__ for a in activities]})
    except Exception as e:
        logger.error(f"Failed to get activities: {str(e)}")
        raise HTTPException(status_code=500, detail="获取活动列表失败")


@router.get("/{activity_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.READ)
async def get_activity(activity_id: int, db: Session = Depends(async_db)):
    """获取活动详情"""
    try:
        service = ActivityService(db, Cache())
        activity = await service.get_activity_by_id(activity_id)
        if not activity:
            raise HTTPException(status_code=404, detail="活动不存在")
        return ResponseModel(data={"activity": activity.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get activity: {str(e)}")
        raise HTTPException(status_code=500, detail="获取活动信息失败")


@router.post("", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.CREATE)
async def create_activity(activity: ActivityCreate, db: Session = Depends(async_db)):
    """创建活动"""
    try:
        service = ActivityService(db, Cache())
        new_activity = await service.create_activity(activity)
        return ResponseModel(message="创建活动成功", data={"activity": new_activity.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create activity: {str(e)}")
        raise HTTPException(status_code=500, detail="创建活动失败")


@router.put("/{activity_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.UPDATE)
async def update_activity(activity_id: int, activity: ActivityUpdate, db: Session = Depends(async_db)):
    """更新活动信息"""
    try:
        service = ActivityService(db, Cache())
        updated_activity = await service.update_activity(activity_id, activity)
        return ResponseModel(message="更新活动成功", data={"activity": updated_activity.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update activity: {str(e)}")
        raise HTTPException(status_code=500, detail="更新活动失败")


@router.delete("/{activity_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.DELETE)
async def delete_activity(activity_id: int, db: Session = Depends(async_db)):
    """删除活动"""
    try:
        service = ActivityService(db, Cache())
        await service.delete_activity(activity_id)
        return ResponseModel(message="删除活动成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to delete activity: {str(e)}")
        raise HTTPException(status_code=500, detail="删除活动失败")


@router.post("/{activity_id}/register", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.UPDATE)
async def register_activity(activity_id: int, user_id: int, db: Session = Depends(async_db)):
    """活动报名"""
    try:
        service = ActivityService(db, Cache())
        registration = await service.register_activity(activity_id, user_id)
        return ResponseModel(message="报名成功", data={"registration": registration.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to register activity: {str(e)}")
        raise HTTPException(status_code=500, detail="活动报名失败")


@router.post("/{activity_id}/cancel", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.UPDATE)
async def cancel_registration(activity_id: int, user_id: int, db: Session = Depends(async_db)):
    """取消报名"""
    try:
        service = ActivityService(db, Cache())
        await service.cancel_registration(activity_id, user_id)
        return ResponseModel(message="取消报名成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to cancel registration: {str(e)}")
        raise HTTPException(status_code=500, detail="取消报名失败")


@router.get("/{activity_id}/participants", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.READ)
async def get_participants(
    activity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(async_db),
):
    """获取活动参与者列表"""
    try:
        service = ActivityService(db, Cache())
        participants = await service.get_participants(activity_id, skip, limit)
        return ResponseModel(data={"participants": [p.__dict__ for p in participants]})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get participants: {str(e)}")
        raise HTTPException(status_code=500, detail="获取参与者列表失败")


@router.post("/{activity_id}/announcements", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.UPDATE)
async def create_announcement(
    activity_id: int, title: str, content: str, publisher_id: int, db: Session = Depends(async_db)
):
    """发布活动通知"""
    try:
        service = ActivityService(db, Cache())
        announcement = await service.create_announcement(activity_id, title, content, publisher_id)
        return ResponseModel(message="发布通知成功", data={"announcement": announcement.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create announcement: {str(e)}")
        raise HTTPException(status_code=500, detail="发布通知失败")


@router.get("/{activity_id}/announcements", response_model=ResponseModel)
@permission.has_permission(ResourceType.ACTIVITY, Action.READ)
async def get_announcements(
    activity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(async_db),
):
    """获取活动通知列表"""
    try:
        service = ActivityService(db, Cache())
        announcements = await service.get_announcements(activity_id, skip, limit)
        return ResponseModel(data={"announcements": [a.__dict__ for a in announcements]})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get announcements: {str(e)}")
        raise HTTPException(status_code=500, detail="获取通知列表失败")
