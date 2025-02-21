from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.course import Course
from models.semester import Semester
from models.teacher import Teacher, TeacherCourse
from schemas.course import CourseResponse, CourseAssign, CourseUpdate

router = APIRouter()


@router.post("/assign", response_model=ResponseSchema[CourseResponse])
async def assign_course(
    course: CourseAssign,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """分配课程"""
    # 检查教师是否存在且在职
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == course.teacher_id,
            Teacher.status == "active",
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or not active")

    # 检查课程是否存在
    if (
        not db.query(Course)
        .filter(
            Course.id == course.course_id,
            Course.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=404, detail="Course not found")

    # 检查学期是否存在
    if (
        not db.query(Semester)
        .filter(
            Semester.id == course.semester_id,
            Semester.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=404, detail="Semester not found")

    # 检查角色是否有效
    valid_roles = ["lecturer", "assistant"]
    if course.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
        )

    # 检查是否已分配该课程
    if (
        db.query(TeacherCourse)
        .filter(
            TeacherCourse.teacher_id == course.teacher_id,
            TeacherCourse.course_id == course.course_id,
            TeacherCourse.semester_id == course.semester_id,
            TeacherCourse.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Course already assigned to this teacher")

    db_course = TeacherCourse(**course.dict(), create_by=current_user)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return success(data=db_course)


@router.get("/{record_id}", response_model=ResponseSchema[CourseResponse])
async def get_course_record(
    record_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取课程记录详情"""
    record = (
        db.query(TeacherCourse)
        .filter(
            TeacherCourse.id == record_id,
            TeacherCourse.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Course record not found")
    return success(data=record)


@router.put("/{record_id}", response_model=ResponseSchema[CourseResponse])
async def update_course_record(
    record_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新课程记录"""
    record = (
        db.query(TeacherCourse)
        .filter(
            TeacherCourse.id == record_id,
            TeacherCourse.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Course record not found")

    # 检查角色是否有效
    if course_update.role:
        valid_roles = ["lecturer", "assistant"]
        if course_update.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
            )

    # 检查状态是否有效
    if course_update.status:
        valid_statuses = ["pending", "confirmed", "completed"]
        if course_update.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

    for field, value in course_update.dict(exclude_unset=True).items():
        setattr(record, field, value)

    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.delete("/{record_id}", response_model=ResponseSchema)
async def delete_course_record(
    record_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除课程记录"""
    record = (
        db.query(TeacherCourse)
        .filter(
            TeacherCourse.id == record_id,
            TeacherCourse.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Course record not found")

    record.is_delete = True
    record.delete_by = current_user
    record.delete_time = datetime.now()

    db.add(record)
    db.commit()
    return success(message="Course record deleted successfully")


@router.get("/", response_model=ResponseSchema[List[CourseResponse]])
async def list_course_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    teacher_id: Optional[int] = None,
    course_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取课程记录列表"""
    query = db.query(TeacherCourse).filter(TeacherCourse.is_delete == False)

    if teacher_id:
        query = query.filter(TeacherCourse.teacher_id == teacher_id)
    if course_id:
        query = query.filter(TeacherCourse.course_id == course_id)
    if semester_id:
        query = query.filter(TeacherCourse.semester_id == semester_id)
    if role:
        query = query.filter(TeacherCourse.role == role)
    if status:
        query = query.filter(TeacherCourse.status == status)

    total = query.count()
    records = query.offset(skip).limit(limit).all()

    return success(data=records, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{record_id}/confirm", response_model=ResponseSchema[CourseResponse])
async def confirm_course(
    record_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """确认课程分配"""
    record = (
        db.query(TeacherCourse)
        .filter(
            TeacherCourse.id == record_id,
            TeacherCourse.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Course record not found")

    if record.status != "pending":
        raise HTTPException(status_code=400, detail="Can only confirm pending courses")

    record.status = "confirmed"
    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.put("/{record_id}/complete", response_model=ResponseSchema[CourseResponse])
async def complete_course(
    record_id: int,
    evaluation_score: Optional[float] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """完成课程"""
    record = (
        db.query(TeacherCourse)
        .filter(
            TeacherCourse.id == record_id,
            TeacherCourse.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Course record not found")

    if record.status != "confirmed":
        raise HTTPException(status_code=400, detail="Can only complete confirmed courses")

    record.status = "completed"
    if evaluation_score is not None:
        record.evaluation_score = evaluation_score
    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.get("/stats", response_model=ResponseSchema)
async def get_course_stats(
    teacher_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取课程统计信息"""
    query = db.query(TeacherCourse).filter(TeacherCourse.is_delete == False)

    if teacher_id:
        query = query.filter(TeacherCourse.teacher_id == teacher_id)
    if semester_id:
        query = query.filter(TeacherCourse.semester_id == semester_id)

    # 角色分布
    role_distribution = {
        role: count
        for role, count in db.query(TeacherCourse.role, func.count(TeacherCourse.id))
        .filter(TeacherCourse.is_delete == False)
        .group_by(TeacherCourse.role)
        .all()
    }

    # ��态分布
    status_distribution = {
        status: count
        for status, count in db.query(TeacherCourse.status, func.count(TeacherCourse.id))
        .filter(TeacherCourse.is_delete == False)
        .group_by(TeacherCourse.status)
        .all()
    }

    # 工作量统计
    workload_stats = (
        db.query(
            func.sum(TeacherCourse.workload).label("total_workload"),
            func.avg(TeacherCourse.workload).label("avg_workload"),
            func.min(TeacherCourse.workload).label("min_workload"),
            func.max(TeacherCourse.workload).label("max_workload"),
        )
        .filter(TeacherCourse.is_delete == False)
        .first()
    )

    # 评教分数统计
    evaluation_stats = (
        db.query(
            func.avg(TeacherCourse.evaluation_score).label("avg_score"),
            func.min(TeacherCourse.evaluation_score).label("min_score"),
            func.max(TeacherCourse.evaluation_score).label("max_score"),
        )
        .filter(
            TeacherCourse.evaluation_score.isnot(None),
            TeacherCourse.is_delete == False,
        )
        .first()
    )

    stats = {
        "role_distribution": role_distribution,
        "status_distribution": status_distribution,
        "workload_stats": {
            "total": workload_stats.total_workload or 0,
            "average": workload_stats.avg_workload or 0,
            "minimum": workload_stats.min_workload or 0,
            "maximum": workload_stats.max_workload or 0,
        },
        "evaluation_stats": {
            "average": evaluation_stats.avg_score or 0,
            "minimum": evaluation_stats.min_score or 0,
            "maximum": evaluation_stats.max_score or 0,
        },
    }

    return success(data=stats)
