from datetime import date, datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.teacher import Teacher, TeacherAttendance
from schemas.teacher import AttendanceResponse, AttendanceCreate, AttendanceUpdate

router = APIRouter()


@router.post("/", response_model=ResponseSchema[AttendanceResponse])
async def create_attendance(
    attendance: AttendanceCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建考勤记录"""
    # 检查教师是否存在且在职
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == attendance.teacher_id,
            Teacher.status == "active",
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or not active")

    # 检查考勤类型是否有效
    valid_types = ["normal", "late", "early", "absent", "leave"]
    if attendance.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid attendance type. Must be one of: {', '.join(valid_types)}",
        )

    # 如果是请假，检查请假类型是否有效
    if attendance.type == "leave":
        if not attendance.leave_type:
            raise HTTPException(
                status_code=400,
                detail="Leave type is required for leave attendance",
            )
        valid_leave_types = ["sick", "personal", "annual", "other"]
        if attendance.leave_type not in valid_leave_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid leave type. Must be one of: {', '.join(valid_leave_types)}",
            )
        if not attendance.leave_reason:
            raise HTTPException(
                status_code=400,
                detail="Leave reason is required for leave attendance",
            )

    # 检查是否已存在当天的考勤记录
    if (
        db.query(TeacherAttendance)
        .filter(
            TeacherAttendance.teacher_id == attendance.teacher_id,
            TeacherAttendance.date == attendance.date,
            TeacherAttendance.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(
            status_code=400,
            detail="Attendance record already exists for this date",
        )

    db_attendance = TeacherAttendance(**attendance.dict(), create_by=current_user)
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return success(data=db_attendance)


@router.get("/{attendance_id}", response_model=ResponseSchema[AttendanceResponse])
async def get_attendance(
    attendance_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考勤记录详情"""
    attendance = (
        db.query(TeacherAttendance)
        .filter(
            TeacherAttendance.id == attendance_id,
            TeacherAttendance.is_delete == False,
        )
        .first()
    )
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return success(data=attendance)


@router.put("/{attendance_id}", response_model=ResponseSchema[AttendanceResponse])
async def update_attendance(
    attendance_id: int,
    attendance_update: AttendanceUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新考勤记录"""
    attendance = (
        db.query(TeacherAttendance)
        .filter(
            TeacherAttendance.id == attendance_id,
            TeacherAttendance.is_delete == False,
        )
        .first()
    )
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    # 检查考勤类型是否有效
    if attendance_update.type:
        valid_types = ["normal", "late", "early", "absent", "leave"]
        if attendance_update.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid attendance type. Must be one of: {', '.join(valid_types)}",
            )

    # 如果更新为请假类型，检查请假类型是否有效
    if attendance_update.type == "leave":
        if not attendance_update.leave_type and not attendance.leave_type:
            raise HTTPException(
                status_code=400,
                detail="Leave type is required for leave attendance",
            )
        if attendance_update.leave_type:
            valid_leave_types = ["sick", "personal", "annual", "other"]
            if attendance_update.leave_type not in valid_leave_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid leave type. Must be one of: {', '.join(valid_leave_types)}",
                )
        if not attendance_update.leave_reason and not attendance.leave_reason:
            raise HTTPException(
                status_code=400,
                detail="Leave reason is required for leave attendance",
            )

    # 检查审批状态是否有效
    if attendance_update.approve_status:
        valid_statuses = ["pending", "approved", "rejected"]
        if attendance_update.approve_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid approve status. Must be one of: {', '.join(valid_statuses)}",
            )

    for field, value in attendance_update.dict(exclude_unset=True).items():
        setattr(attendance, field, value)

    attendance.update_by = current_user
    attendance.update_time = datetime.now()

    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return success(data=attendance)


@router.delete("/{attendance_id}", response_model=ResponseSchema)
async def delete_attendance(
    attendance_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除考勤记录"""
    attendance = (
        db.query(TeacherAttendance)
        .filter(
            TeacherAttendance.id == attendance_id,
            TeacherAttendance.is_delete == False,
        )
        .first()
    )
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    attendance.is_delete = True
    attendance.delete_by = current_user
    attendance.delete_time = datetime.now()

    db.add(attendance)
    db.commit()
    return success(message="Attendance record deleted successfully")


@router.get("/", response_model=ResponseSchema[List[AttendanceResponse]])
async def list_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    teacher_id: Optional[int] = None,
    type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    approve_status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考勤记录列表"""
    query = db.query(TeacherAttendance).filter(TeacherAttendance.is_delete == False)

    if teacher_id:
        query = query.filter(TeacherAttendance.teacher_id == teacher_id)
    if type:
        query = query.filter(TeacherAttendance.type == type)
    if start_date:
        query = query.filter(TeacherAttendance.date >= start_date)
    if end_date:
        query = query.filter(TeacherAttendance.date <= end_date)
    if approve_status:
        query = query.filter(TeacherAttendance.approve_status == approve_status)

    total = query.count()
    attendance_records = query.offset(skip).limit(limit).all()

    return success(data=attendance_records, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{attendance_id}/approve", response_model=ResponseSchema[AttendanceResponse])
async def approve_attendance(
    attendance_id: int,
    approve_status: str,
    comments: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """审批考勤记录"""
    attendance = (
        db.query(TeacherAttendance)
        .filter(
            TeacherAttendance.id == attendance_id,
            TeacherAttendance.is_delete == False,
        )
        .first()
    )
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    if attendance.approve_status != "pending":
        raise HTTPException(status_code=400, detail="Can only approve pending attendance records")

    valid_statuses = ["approved", "rejected"]
    if approve_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid approve status. Must be one of: {', '.join(valid_statuses)}",
        )

    attendance.approve_status = approve_status
    attendance.approve_comments = comments
    attendance.approver_id = current_user
    attendance.approve_time = datetime.now()
    attendance.update_by = current_user
    attendance.update_time = datetime.now()

    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return success(data=attendance)


@router.post("/check-in", response_model=ResponseSchema[AttendanceResponse])
async def check_in(
    teacher_id: int,
    location: Optional[str] = None,
    device: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """教师签到"""
    # 检查教师是否存在且在职
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id,
            Teacher.status == "active",
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or not active")

    # 检查是否已存在当天的考勤记录
    today = date.today()
    attendance = (
        db.query(TeacherAttendance)
        .filter(
            TeacherAttendance.teacher_id == teacher_id,
            TeacherAttendance.date == today,
            TeacherAttendance.is_delete == False,
        )
        .first()
    )

    if attendance:
        if attendance.check_in_time:
            raise HTTPException(status_code=400, detail="Already checked in today")
    else:
        attendance = TeacherAttendance(
            teacher_id=teacher_id,
            date=today,
            type="normal",
            create_by=current_user,
        )

    now = datetime.now()
    attendance.check_in_time = now
    attendance.location = location
    attendance.device = device

    # 判断是否迟到
    work_start_time = datetime.combine(today, time(9, 0))  # 假设上班时间为9:00
    if now > work_start_time:
        attendance.type = "late"

    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return success(data=attendance)


@router.post("/check-out", response_model=ResponseSchema[AttendanceResponse])
async def check_out(
    teacher_id: int,
    location: Optional[str] = None,
    device: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """教师签退"""
    # 检查教师是否存在且在职
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id,
            Teacher.status == "active",
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found or not active",
        )

    # 获取当天的考勤记录
    today = date.today()
    attendance = (
        db.query(TeacherAttendance)
        .filter(
            TeacherAttendance.teacher_id == teacher_id,
            TeacherAttendance.date == today,
            TeacherAttendance.is_delete == False,
        )
        .first()
    )

    if not attendance:
        raise HTTPException(status_code=400, detail="No check-in record found today")
    if not attendance.check_in_time:
        raise HTTPException(status_code=400, detail="Must check in first")
    if attendance.check_out_time:
        raise HTTPException(status_code=400, detail="Already checked out today")

    now = datetime.now()
    attendance.check_out_time = now
    attendance.location = location or attendance.location
    attendance.device = device or attendance.device

    # 判断是否早退
    work_end_time = datetime.combine(today, time(17, 0))  # 假设下班时间为17:00
    if now < work_end_time:
        attendance.type = "early"

    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return success(data=attendance)


@router.post("/leave", response_model=ResponseSchema[AttendanceResponse])
async def apply_leave(
    teacher_id: int,
    date: date,
    leave_type: str,
    leave_reason: str,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """申请请假"""
    # 检查教师是否存在且在职
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id,
            Teacher.status == "active",
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or not active")

    # 检查请假类型是否有效
    valid_leave_types = ["sick", "personal", "annual", "other"]
    if leave_type not in valid_leave_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid leave type. Must be one of: {', '.join(valid_leave_types)}",
        )

    # 检查是否已存在当天的考勤记录
    if (
        db.query(TeacherAttendance)
        .filter(
            TeacherAttendance.teacher_id == teacher_id,
            TeacherAttendance.date == date,
            TeacherAttendance.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(
            status_code=400,
            detail="Attendance record already exists for this date",
        )

    attendance = TeacherAttendance(
        teacher_id=teacher_id,
        date=date,
        type="leave",
        leave_type=leave_type,
        leave_reason=leave_reason,
        create_by=current_user,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return success(data=attendance)


@router.get("/stats", response_model=ResponseSchema)
async def get_attendance_stats(
    teacher_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考勤统计信息"""
    query = db.query(TeacherAttendance).filter(TeacherAttendance.is_delete == False)

    if teacher_id:
        query = query.filter(TeacherAttendance.teacher_id == teacher_id)
    if start_date:
        query = query.filter(TeacherAttendance.date >= start_date)
    if end_date:
        query = query.filter(TeacherAttendance.date <= end_date)

    # 考勤类型分布
    type_distribution = {
        type: count
        for type, count in db.query(
            TeacherAttendance.type,
            func.count(TeacherAttendance.id),
        )
        .filter(TeacherAttendance.is_delete == False)
        .group_by(TeacherAttendance.type)
        .all()
    }

    # 请假类型分布
    leave_type_distribution = {
        leave_type: count
        for leave_type, count in db.query(
            TeacherAttendance.leave_type,
            func.count(TeacherAttendance.id),
        )
        .filter(
            TeacherAttendance.type == "leave",
            TeacherAttendance.is_delete == False,
        )
        .group_by(TeacherAttendance.leave_type)
        .all()
    }

    # 审批状态分布
    approve_status_distribution = {
        status: count
        for status, count in db.query(
            TeacherAttendance.approve_status,
            func.count(TeacherAttendance.id),
        )
        .filter(TeacherAttendance.is_delete == False)
        .group_by(TeacherAttendance.approve_status)
        .all()
    }

    # 按月统计
    month_distribution = {
        month: count
        for month, count in db.query(
            extract("month", TeacherAttendance.date),
            func.count(TeacherAttendance.id),
        )
        .filter(TeacherAttendance.is_delete == False)
        .group_by(extract("month", TeacherAttendance.date))
        .all()
    }

    stats = {
        "type_distribution": type_distribution,
        "leave_type_distribution": leave_type_distribution,
        "approve_status_distribution": approve_status_distribution,
        "month_distribution": month_distribution,
    }

    return success(data=stats)
