from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.cache import Cache
from core.validators import ActivityCreate, ActivityUpdate
from models.activity import Activity


class ActivityService:
    def __init__(self, db: Session, cache: Cache):
        self.db = db
        self.cache = cache

    async def get_activities(
        self, skip: int = 0, limit: int = 100, type: str = None, is_public: bool = None, organizer_id: int = None
    ) -> List[Activity]:
        query = self.db.query(Activity)
        if type:
            query = query.filter(Activity.type == type)
        if is_public is not None:
            query = query.filter(Activity.is_public == is_public)
        if organizer_id:
            query = query.filter(Activity.organizer_id == organizer_id)
        return query.offset(skip).limit(limit).all()

    async def get_activity_by_id(self, activity_id: int) -> Optional[Activity]:
        return self.db.query(Activity).filter(Activity.id == activity_id).first()

    async def create_activity(self, activity: ActivityCreate) -> Activity:
        db_activity = Activity(**activity.dict())
        self.db.add(db_activity)
        self.db.commit()
        self.db.refresh(db_activity)
        return db_activity

    async def update_activity(self, activity_id: int, activity: ActivityUpdate) -> Activity:
        db_activity = await self.get_activity_by_id(activity_id)
        if not db_activity:
            raise HTTPException(status_code=404, detail="活动不存在")

        for field, value in activity.dict(exclude_unset=True).items():
            setattr(db_activity, field, value)

        self.db.commit()
        self.db.refresh(db_activity)
        return db_activity

    async def delete_activity(self, activity_id: int) -> None:
        db_activity = await self.get_activity_by_id(activity_id)
        if not db_activity:
            raise HTTPException(status_code=404, detail="活动不存在")

        self.db.delete(db_activity)
        self.db.commit()

    async def register_activity(self, activity_id: int, user_id: int):
        pass

    async def cancel_registration(self, activity_id: int, user_id: int):
        pass

    async def get_participants(self, activity_id: int, skip: int = 0, limit: int = 100):
        pass

    async def create_announcement(self, activity_id: int, title: str, content: str, publisher_id: int):
        pass

    async def get_announcements(self, activity_id: int, skip: int = 0, limit: int = 100):
        pass
