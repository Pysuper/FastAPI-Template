from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.endpoints.academic.students.courses import StudentCourse
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.course import Course
from models.semester import Semester
from models.student import Student
from schemas.grade import *
from models.student import StudentGrade

router = APIRouter()


@router.post("/", response_model=ResponseSchema[GradeResponse])
async def create_grade(
    grade: GradeCreate, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """创建成绩记录"""
    # 检查学生是否存在
    if not db.query(Student).filter(Student.id == grade.student_id, Student.is_delete == False).first():
        raise HTTPException(status_code=404, detail="Student not found")

    # 检查课程是否存在
    if not db.query(Course).filter(Course.id == grade.course_id, Course.is_delete == False).first():
        raise HTTPException(status_code=404, detail="Course not found")

    # 检查学期是否存在
    if not db.query(Semester).filter(Semester.id == grade.semester_id, Semester.is_delete == False).first():
        raise HTTPException(status_code=404, detail="Semester not found")

    # 检查是否已存在成绩记录
    if (
        db.query(StudentGrade)
        .filter(
            StudentGrade.student_id == grade.student_id,
            StudentGrade.course_id == grade.course_id,
            StudentGrade.semester_id == grade.semester_id,
            StudentGrade.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Grade record already exists")

    # 检查成绩等级是否有效
    valid_levels = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]
    if grade.grade_level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid grade level. Must be one of: {', '.join(valid_levels)}")

    db_grade = StudentGrade(**grade.dict(), create_by=current_user)
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return success(data=db_grade)


@router.get("/{grade_id}", response_model=ResponseSchema[GradeResponse])
async def get_grade(grade_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取成绩记录详情"""
    grade = db.query(StudentGrade).filter(StudentGrade.id == grade_id, StudentGrade.is_delete == False).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade record not found")

    # 检查访问权限
    if not is_admin(current_user) and grade.student_id != current_user:
        raise HTTPException(status_code=403, detail="Permission denied")

    return success(data=grade)


@router.put("/{grade_id}", response_model=ResponseSchema[GradeResponse])
async def update_grade(
    grade_id: int,
    grade_update: GradeUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新成绩记录"""
    # 检查是否有权限
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    grade = db.query(StudentGrade).filter(StudentGrade.id == grade_id, StudentGrade.is_delete == False).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade record not found")

    # 只能更新草稿状态的成绩
    if grade.status != "draft":
        raise HTTPException(status_code=400, detail="Can only update draft grades")

    # 检查成绩等级是否有效
    if grade_update.grade_level:
        valid_levels = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]
        if grade_update.grade_level not in valid_levels:
            raise HTTPException(
                status_code=400, detail=f"Invalid grade level. Must be one of: {', '.join(valid_levels)}"
            )

    for field, value in grade_update.dict(exclude_unset=True).items():
        setattr(grade, field, value)

    grade.update_by = current_user
    grade.update_time = datetime.now()

    db.add(grade)
    db.commit()
    db.refresh(grade)
    return success(data=grade)


@router.delete("/{grade_id}", response_model=ResponseSchema)
async def delete_grade(grade_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """删除成绩记录"""
    # 检查是否有权限
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    grade = db.query(StudentGrade).filter(StudentGrade.id == grade_id, StudentGrade.is_delete == False).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade record not found")

    # 只能删除草稿状态的成绩
    if grade.status != "draft":
        raise HTTPException(status_code=400, detail="Can only delete draft grades")

    grade.is_delete = True
    grade.delete_by = current_user
    grade.delete_time = datetime.now()

    db.add(grade)
    db.commit()
    return success(message="Grade record deleted successfully")


@router.get("/", response_model=ResponseSchema[List[GradeResponse]])
async def list_grades(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    grade_level: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取成绩记录列表"""
    query = db.query(StudentGrade).filter(StudentGrade.is_delete == False)

    # 非管理员只能查看自己的成绩
    if not is_admin(current_user):
        query = query.filter(StudentGrade.student_id == current_user)
    else:
        if student_id:
            query = query.filter(StudentGrade.student_id == student_id)

    if course_id:
        query = query.filter(StudentGrade.course_id == course_id)
    if semester_id:
        query = query.filter(StudentGrade.semester_id == semester_id)
    if status:
        query = query.filter(StudentGrade.status == status)
    if min_score is not None:
        query = query.filter(StudentGrade.score >= min_score)
    if max_score is not None:
        query = query.filter(StudentGrade.score <= max_score)
    if grade_level:
        query = query.filter(StudentGrade.grade_level == grade_level)

    total = query.count()
    grades = query.offset(skip).limit(limit).all()

    return success(data=grades, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{grade_id}/submit", response_model=ResponseSchema[GradeResponse])
async def submit_grade(grade_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """提交成绩记录"""
    # 检查是否有权限
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    grade = db.query(StudentGrade).filter(StudentGrade.id == grade_id, StudentGrade.is_delete == False).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade record not found")

    if grade.status != "draft":
        raise HTTPException(status_code=400, detail="Can only submit draft grades")

    grade.status = "submitted"
    grade.update_by = current_user
    grade.update_time = datetime.now()

    db.add(grade)
    db.commit()
    db.refresh(grade)
    return success(data=grade)


@router.put("/{grade_id}/confirm", response_model=ResponseSchema[GradeResponse])
async def confirm_grade(grade_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """确认成绩记录"""
    # 检查是否有权限
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    grade = db.query(StudentGrade).filter(StudentGrade.id == grade_id, StudentGrade.is_delete == False).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade record not found")

    if grade.status != "submitted":
        raise HTTPException(status_code=400, detail="Can only confirm submitted grades")

    grade.status = "confirmed"
    grade.update_by = current_user
    grade.update_time = datetime.now()

    # 更新选课记录状态和成绩
    course_record = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.student_id == grade.student_id,
            StudentCourse.course_id == grade.course_id,
            StudentCourse.semester_id == grade.semester_id,
            StudentCourse.is_delete == False,
        )
        .first()
    )
    if course_record:
        course_record.status = "completed"
        course_record.score = grade.score
        course_record.grade_point = grade.grade_point
        course_record.update_by = current_user
        course_record.update_time = datetime.now()
        db.add(course_record)

    db.add(grade)
    db.commit()
    db.refresh(grade)
    return success(data=grade)


@router.get("/stats", response_model=ResponseSchema)
async def get_grade_stats(
    student_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取成绩统计信息"""
    # 非管理员只能查看自己的成绩统计
    if not is_admin(current_user):
        student_id = current_user
    elif not student_id:
        raise HTTPException(status_code=400, detail="Student ID is required")

    query = db.query(StudentGrade).filter(
        StudentGrade.student_id == student_id, StudentGrade.status == "confirmed", StudentGrade.is_delete == False
    )

    if semester_id:
        query = query.filter(StudentGrade.semester_id == semester_id)

    # 总体统计
    total_courses = query.count()
    if total_courses == 0:
        return success(
            data={
                "total_courses": 0,
                "total_credits": 0,
                "average_score": 0,
                "average_gpa": 0,
                "score_distribution": {},
                "grade_distribution": {},
            }
        )

    # 学分统计
    total_credits = (
        db.session.query(func.sum(Course.credits))
        .join(StudentGrade, Course.id == StudentGrade.course_id)
        .filter(
            StudentGrade.student_id == student_id, StudentGrade.status == "confirmed", StudentGrade.is_delete == False
        )
        .scalar()
        or 0
    )

    # 平均分和平均绩点
    avg_score = (
        db.session.query(func.avg(StudentGrade.score))
        .filter(
            StudentGrade.student_id == student_id, StudentGrade.status == "confirmed", StudentGrade.is_delete == False
        )
        .scalar()
        or 0
    )

    avg_gpa = (
        db.session.query(func.avg(StudentGrade.grade_point))
        .filter(
            StudentGrade.student_id == student_id, StudentGrade.status == "confirmed", StudentGrade.is_delete == False
        )
        .scalar()
        or 0
    )

    # 分数分布
    score_ranges = [(0, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
    score_distribution = {}
    for start, end in score_ranges:
        count = query.filter(StudentGrade.score >= start, StudentGrade.score < end).count()
        score_distribution[f"{start}-{end}"] = count

    # 等级分布
    grade_distribution = {
        grade: count
        for grade, count in db.session.query(StudentGrade.grade_level, func.count(StudentGrade.id))
        .filter(
            StudentGrade.student_id == student_id, StudentGrade.status == "confirmed", StudentGrade.is_delete == False
        )
        .group_by(StudentGrade.grade_level)
        .all()
    }

    stats = {
        "total_courses": total_courses,
        "total_credits": total_credits,
        "average_score": avg_score,
        "average_gpa": avg_gpa,
        "score_distribution": score_distribution,
        "grade_distribution": grade_distribution,
    }

    return success(data=stats)
