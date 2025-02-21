from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_active_user
from core.exceptions import NotFoundException
from core.schemas.common import Response, PageResponse
from dependencies.db import get_db
from schemas.auth import User
from schemas.course import (
    CourseScheduleCreate,
    CourseScheduleUpdate,
    CourseScheduleResponse,
    CourseScheduleStatusUpdate,
    CourseScheduleRoomUpdate,
    CourseScheduleTeacherUpdate,
)

router = APIRouter(prefix="/courses/{course_id}/schedules", tags=["课程安排"])


def CourseScheduleService(db):
    pass


@router.get("/", response_model=PageResponse[CourseScheduleResponse], summary="获取课程安排列表")
async def get_schedules(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    status: str = Query(None, description="状态"),
    teacher_id: int = Query(None, description="教师ID"),
    room_id: int = Query(None, description="教室ID"),
    day_of_week: int = Query(None, description="星期几"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query(None, description="排序字段"),
    order: str = Query("desc", description="排序方向"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取课程安排列表"""
    service = CourseScheduleService(db)
    total, items = service.get_schedules(
        course_id=course_id,
        semester=semester,
        status=status,
        teacher_id=teacher_id,
        room_id=room_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
        sort=sort,
        order=order,
    )
    return PageResponse(total=total, items=items, page=page, size=size)


@router.post("/", response_model=Response, summary="创建课程安排")
async def create_schedule(
    course_id: int = Path(..., description="课程ID"),
    data: CourseScheduleCreate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建课程安排"""
    service = CourseScheduleService(db)
    schedule = service.create_schedule(course_id, data)
    return Response(data={"id": schedule.id})


@router.get("/{id}", response_model=Response, summary="获取课程安排详情")
async def get_schedule(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="课程安排ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取课程安排详情"""
    service = CourseScheduleService(db)
    schedule = service.get_schedule(course_id, id)
    if not schedule:
        raise NotFoundException("课程安排不存在")
    return Response(data=schedule)


@router.put("/{id}", response_model=Response, summary="更新课程安排")
async def update_schedule(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="课程安排ID"),
    data: CourseScheduleUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新课程安排"""
    service = CourseScheduleService(db)
    schedule = service.update_schedule(course_id, id, data)
    return Response()


@router.delete("/{id}", response_model=Response, summary="删除课程安排")
async def delete_schedule(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="课程安排ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除课程安排"""
    service = CourseScheduleService(db)
    service.delete_schedule(course_id, id)
    return Response()


@router.put("/{id}/status", response_model=Response, summary="更新课程安排状态")
async def update_schedule_status(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="课程安排ID"),
    data: CourseScheduleStatusUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新课程安排状态"""
    service = CourseScheduleService(db)
    service.update_schedule_status(course_id, id, data.status)
    return Response()


@router.put("/{id}/room", response_model=Response, summary="更新课程安排教室")
async def update_schedule_room(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="课程安排ID"),
    data: CourseScheduleRoomUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新课程安排教室"""
    service = CourseScheduleService(db)
    service.update_schedule_room(course_id, id, data.room_id)
    return Response()


@router.put("/{id}/teacher", response_model=Response, summary="更新课程安排教师")
async def update_schedule_teacher(
    course_id: int = Path(..., description="课程ID"),
    id: int = Path(..., description="课程安排ID"),
    data: CourseScheduleTeacherUpdate = Body(...),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新课程安排教师"""
    service = CourseScheduleService(db)
    service.update_schedule_teacher(course_id, id, data.teacher_id)
    return Response()


@router.get("/rooms", response_model=Response, summary="获取可用教室列表")
async def get_available_rooms(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(..., description="学期"),
    day_of_week: int = Query(..., description="星期几"),
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取可用教室列��"""
    service = CourseScheduleService(db)
    rooms = service.get_available_rooms(
        course_id=course_id, semester=semester, day_of_week=day_of_week, start_time=start_time, end_time=end_time
    )
    return Response(data=rooms)


@router.get("/teachers", response_model=Response, summary="获取可用教师列表")
async def get_available_teachers(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(..., description="学期"),
    day_of_week: int = Query(..., description="星期几"),
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取可用教师列表"""
    service = CourseScheduleService(db)
    teachers = service.get_available_teachers(
        course_id=course_id, semester=semester, day_of_week=day_of_week, start_time=start_time, end_time=end_time
    )
    return Response(data=teachers)


@router.get("/conflicts", response_model=Response, summary="获取课程安排冲突")
async def get_schedule_conflicts(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(..., description="学期"),
    day_of_week: int = Query(..., description="星期几"),
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    room_id: int = Query(None, description="教室ID"),
    teacher_id: int = Query(None, description="教师ID"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取课程安排冲突"""
    service = CourseScheduleService(db)
    conflicts = service.get_schedule_conflicts(
        course_id=course_id,
        semester=semester,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room_id=room_id,
        teacher_id=teacher_id,
    )
    return Response(data=conflicts)


@router.get("/stats", response_model=Response, summary="获取课程安排统计")
async def get_schedule_stats(
    course_id: int = Path(..., description="课程ID"),
    semester: str = Query(None, description="学期"),
    start_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    db: Session = Depends(async_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取课程安排统计"""
    service = CourseScheduleService(db)
    stats = service.get_schedule_stats(course_id=course_id, semester=semester, start_time=start_time, end_time=end_time)
    return Response(data=stats)
