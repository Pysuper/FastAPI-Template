from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.course import Course
from models.semester import Semester
from models.student import Student
from models.student import StudentCourse
from schemas.course import *

# 路由
router = APIRouter()


@router.post("/select", response_model=ResponseSchema[CourseResponse])
async def select_course(
    course: CourseSelect,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """学生选课"""
    # 检查课程是否存在
    db_course = db.query(Course).filter(Course.id == course.course_id, Course.is_delete == False).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 检查学期是否存在
    semester = db.query(Semester).filter(Semester.id == course.semester_id, Semester.is_delete == False).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")

    # 检查是否已选过该课程
    if (
        db.query(StudentCourse)
        .filter(
            StudentCourse.student_id == current_user,
            StudentCourse.course_id == course.course_id,
            StudentCourse.semester_id == course.semester_id,
            StudentCourse.status != "dropped",
            StudentCourse.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Course already selected")

    # 检查课程容量
    selected_count = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.course_id == course.course_id,
            StudentCourse.semester_id == course.semester_id,
            StudentCourse.status != "dropped",
            StudentCourse.is_delete == False,
        )
        .count()
    )
    if selected_count >= db_course.capacity:
        raise HTTPException(status_code=400, detail="Course is full")

    # 检查选课时间
    now = datetime.now()
    if now < semester.select_start_time or now > semester.select_end_time:
        raise HTTPException(status_code=400, detail="Not in course selection period")

    # 检查先修课程
    if db_course.prerequisites:
        for prereq_id in db_course.prerequisites:
            completed = (
                db.query(StudentCourse)
                .filter(
                    StudentCourse.student_id == current_user,
                    StudentCourse.course_id == prereq_id,
                    StudentCourse.status == "completed",
                    StudentCourse.is_delete == False,
                )
                .first()
            )
            if not completed:
                prereq = db.query(Course).filter(Course.id == prereq_id).first()
                raise HTTPException(
                    status_code=400, detail=f"Prerequisite course not completed: {prereq.name if prereq else prereq_id}"
                )

    db_record = StudentCourse(
        student_id=current_user, course_id=course.course_id, semester_id=course.semester_id, create_by=current_user
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return success(data=db_record)


@router.post("/drop/{record_id}", response_model=ResponseSchema[CourseResponse])
async def drop_course(record_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """退选课程"""
    record = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.id == record_id, StudentCourse.student_id == current_user, StudentCourse.is_delete == False
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Course record not found")

    if record.status != "selected":
        raise HTTPException(status_code=400, detail="Can only drop selected courses")

    # 检查退选时间
    semester = db.query(Semester).filter(Semester.id == record.semester_id).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")

    now = datetime.now()
    if now < semester.drop_start_time or now > semester.drop_end_time:
        raise HTTPException(status_code=400, detail="Not in course dropping period")

    record.status = "dropped"
    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.get("/records/{record_id}", response_model=ResponseSchema[CourseResponse])
async def get_course_record(
    record_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """获取选课记录详情"""
    record = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.id == record_id, StudentCourse.student_id == current_user, StudentCourse.is_delete == False
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Course record not found")
    return success(data=record)


@router.get("/records", response_model=ResponseSchema[List[CourseResponse]])
async def list_course_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    semester_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取选课记录列表"""
    query = db.query(StudentCourse).filter(StudentCourse.student_id == current_user, StudentCourse.is_delete == False)

    if semester_id:
        query = query.filter(StudentCourse.semester_id == semester_id)
    if status:
        query = query.filter(StudentCourse.status == status)

    total = query.count()
    records = query.offset(skip).limit(limit).all()

    return success(data=records, meta={"total": total, "skip": skip, "limit": limit})


@router.get("/available", response_model=ResponseSchema[List[dict]])
async def list_available_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    semester_id: int = None,
    keyword: Optional[str] = None,
    department_id: Optional[int] = None,
    course_type: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取可选课程列表"""
    # 检查学期是否存在且在选课时间内
    semester = db.query(Semester).filter(Semester.id == semester_id, Semester.is_delete == False).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")

    now = datetime.now()
    if now < semester.select_start_time or now > semester.select_end_time:
        raise HTTPException(status_code=400, detail="Not in course selection period")

    # 获取学生信息
    student = db.query(Student).filter(Student.id == current_user).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 查询可选课程
    query = db.query(Course).filter(Course.is_delete == False)

    if keyword:
        query = query.filter(or_(Course.name.ilike(f"%{keyword}%"), Course.code.ilike(f"%{keyword}%")))
    if department_id:
        query = query.filter(Course.department_id == department_id)
    if course_type:
        query = query.filter(Course.course_type == course_type)

    # 排除已选课程
    selected_courses = (
        db.query(StudentCourse.course_id)
        .filter(
            StudentCourse.student_id == current_user,
            StudentCourse.semester_id == semester_id,
            StudentCourse.status != "dropped",
            StudentCourse.is_delete == False,
        )
        .all()
    )
    selected_course_ids = [c.course_id for c in selected_courses]
    if selected_course_ids:
        query = query.filter(Course.id.notin_(selected_course_ids))

    total = query.count()
    courses = query.offset(skip).limit(limit).all()

    # 获取每个课程的选课人数
    course_counts = {
        c.id: db.query(StudentCourse)
        .filter(
            StudentCourse.course_id == c.id,
            StudentCourse.semester_id == semester_id,
            StudentCourse.status != "dropped",
            StudentCourse.is_delete == False,
        )
        .count()
        for c in courses
    }

    # 检查先修课程是否完成
    completed_courses = set(
        c.course_id
        for c in db.query(StudentCourse)
        .filter(
            StudentCourse.student_id == current_user,
            StudentCourse.status == "completed",
            StudentCourse.is_delete == False,
        )
        .all()
    )

    result = []
    for course in courses:
        # 检查是否满足先修要求
        prerequisites_met = True
        missing_prerequisites = []
        if course.prerequisites:
            for prereq_id in course.prerequisites:
                if prereq_id not in completed_courses:
                    prerequisites_met = False
                    prereq = db.query(Course).filter(Course.id == prereq_id).first()
                    missing_prerequisites.append(prereq.name if prereq else str(prereq_id))

        result.append(
            {
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "credits": course.credits,
                "course_type": course.course_type,
                "department_id": course.department_id,
                "capacity": course.capacity,
                "selected_count": course_counts[course.id],
                "prerequisites_met": prerequisites_met,
                "missing_prerequisites": missing_prerequisites if not prerequisites_met else [],
            }
        )

    return success(data=result, meta={"total": total, "skip": skip, "limit": limit})


@router.get("/stats", response_model=ResponseSchema)
async def get_course_stats(
    semester_id: Optional[int] = None, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """获取选课��计信息"""
    query = db.query(StudentCourse).filter(StudentCourse.student_id == current_user, StudentCourse.is_delete == False)

    if semester_id:
        query = query.filter(StudentCourse.semester_id == semester_id)

    # 总体统计
    total_courses = query.count()
    completed_courses = query.filter(StudentCourse.status == "completed").count()
    selected_courses = query.filter(StudentCourse.status == "selected").count()
    dropped_courses = query.filter(StudentCourse.status == "dropped").count()

    # 学分统计
    completed_credits = (
        db.session.query(func.sum(Course.credits))
        .join(StudentCourse, Course.id == StudentCourse.course_id)
        .filter(
            StudentCourse.student_id == current_user,
            StudentCourse.status == "completed",
            StudentCourse.is_delete == False,
        )
        .scalar()
        or 0
    )

    selected_credits = (
        db.session.query(func.sum(Course.credits))
        .join(StudentCourse, Course.id == StudentCourse.course_id)
        .filter(
            StudentCourse.student_id == current_user,
            StudentCourse.status == "selected",
            StudentCourse.is_delete == False,
        )
        .scalar()
        or 0
    )

    # 成绩统计
    scores = [
        record.score
        for record in query.filter(StudentCourse.status == "completed", StudentCourse.score.isnot(None)).all()
    ]

    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0

    # 绩点统计
    grade_points = [
        record.grade_point
        for record in query.filter(StudentCourse.status == "completed", StudentCourse.grade_point.isnot(None)).all()
    ]

    avg_gpa = sum(grade_points) / len(grade_points) if grade_points else 0

    stats = {
        "total_courses": total_courses,
        "completed_courses": completed_courses,
        "selected_courses": selected_courses,
        "dropped_courses": dropped_courses,
        "completed_credits": completed_credits,
        "selected_credits": selected_credits,
        "total_credits": completed_credits + selected_credits,
        "average_score": avg_score,
        "max_score": max_score,
        "min_score": min_score,
        "average_gpa": avg_gpa,
    }

    return success(data=stats)
