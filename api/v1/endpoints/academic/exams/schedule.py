from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.exam import ExamSchedule
from schemas.exam import ExamBase, ExamScheduleCreate, ExamScheduleResponse, ExamScheduleUpdate

router = APIRouter()


@router.post("/", response_model=ResponseSchema[ExamScheduleResponse])
async def create_schedule(
    schedule: ExamScheduleCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建考试安排"""
    # 检查考试是否存在
    exam = db.query(ExamBase).filter(ExamBase.id == schedule.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # 检查考场是否可用
    room_available = check_room_availability(
        db,
        schedule.room_id,
        schedule.start_time,
        schedule.end_time,
    )
    if not room_available:
        raise HTTPException(status_code=400, detail="Room not available")

    # 检查监考教师是否可用
    invigilator_available = check_invigilator_availability(
        db, schedule.invigilator_id, schedule.start_time, schedule.end_time
    )
    if not invigilator_available:
        raise HTTPException(status_code=400, detail="Invigilator not available")

    db_schedule = ExamSchedule(**schedule.dict(), create_by=current_user)
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return success(data=db_schedule)


@router.get("/{schedule_id}", response_model=ResponseSchema[ExamScheduleResponse])
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考试安排详情"""
    schedule = db.query(ExamSchedule).filter(ExamSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return success(data=schedule)


@router.put("/{schedule_id}", response_model=ResponseSchema[ExamScheduleResponse])
async def update_schedule(
    schedule_id: int,
    schedule_update: ExamScheduleUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新考试安排"""
    schedule = db.query(ExamSchedule).filter(ExamSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # 如果更新了考场或时间，需要检查可用性
    if schedule_update.room_id or schedule_update.start_time or schedule_update.end_time:
        room_id = schedule_update.room_id or schedule.room_id
        start_time = schedule_update.start_time or schedule.start_time
        end_time = schedule_update.end_time or schedule.end_time

        room_available = check_room_availability(
            db,
            room_id,
            start_time,
            end_time,
            exclude_schedule_id=schedule_id,
        )
        if not room_available:
            raise HTTPException(status_code=400, detail="Room not available")

    # 如果更新了监考教师或时间，需要检查可用性
    if schedule_update.invigilator_id or schedule_update.start_time or schedule_update.end_time:
        invigilator_id = schedule_update.invigilator_id or schedule.invigilator_id
        start_time = schedule_update.start_time or schedule.start_time
        end_time = schedule_update.end_time or schedule.end_time

        invigilator_available = check_invigilator_availability(
            db,
            invigilator_id,
            start_time,
            end_time,
            exclude_schedule_id=schedule_id,
        )
        if not invigilator_available:
            raise HTTPException(status_code=400, detail="Invigilator not available")

    for field, value in schedule_update.dict(exclude_unset=True).items():
        setattr(schedule, field, value)

    schedule.update_by = current_user
    schedule.update_time = datetime.now()

    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return success(data=schedule)


@router.delete("/{schedule_id}", response_model=ResponseSchema)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除考试安排"""
    schedule = db.query(ExamSchedule).filter(ExamSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.is_delete = True
    schedule.delete_by = current_user
    schedule.delete_time = datetime.now()

    db.add(schedule)
    db.commit()
    return success(message="Schedule deleted successfully")


@router.get("/", response_model=ResponseSchema[List[ExamScheduleResponse]])
async def list_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    exam_id: Optional[int] = None,
    room_id: Optional[int] = None,
    invigilator_id: Optional[int] = None,
    status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考试安排列表"""
    query = db.query(ExamSchedule).filter(ExamSchedule.is_delete == False)

    if exam_id:
        query = query.filter(ExamSchedule.exam_id == exam_id)
    if room_id:
        query = query.filter(ExamSchedule.room_id == room_id)
    if invigilator_id:
        query = query.filter(ExamSchedule.invigilator_id == invigilator_id)
    if status:
        query = query.filter(ExamSchedule.status == status)
    if start_time:
        query = query.filter(ExamSchedule.start_time >= start_time)
    if end_time:
        query = query.filter(ExamSchedule.end_time <= end_time)

    total = query.count()
    schedules = query.offset(skip).limit(limit).all()

    return success(data=schedules, meta={"total": total, "skip": skip, "limit": limit})


# 辅助函数
def check_room_availability(
    db: Session,
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_schedule_id: Optional[int] = None,
) -> bool:
    """检查考场在指定时间段是否可用"""
    query = db.query(ExamSchedule).filter(
        ExamSchedule.room_id == room_id,
        ExamSchedule.is_delete == False,
        ExamSchedule.status != "finished",
        # 检查时间段是否重叠
        ExamSchedule.start_time < end_time,
        ExamSchedule.end_time > start_time,
    )

    if exclude_schedule_id:
        query = query.filter(ExamSchedule.id != exclude_schedule_id)

    return query.count() == 0


def check_invigilator_availability(
    db: Session,
    invigilator_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_schedule_id: Optional[int] = None,
) -> bool:
    """检查监考教师在指定时间段是否可用"""
    query = db.query(ExamSchedule).filter(
        ExamSchedule.invigilator_id == invigilator_id,
        ExamSchedule.is_delete == False,
        ExamSchedule.status != "finished",
        # 检查时间段是否重叠
        ExamSchedule.start_time < end_time,
        ExamSchedule.end_time > start_time,
    )

    if exclude_schedule_id:
        query = query.filter(ExamSchedule.id != exclude_schedule_id)

    return query.count() == 0
