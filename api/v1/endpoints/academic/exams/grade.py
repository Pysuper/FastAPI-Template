from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.v1.endpoints.academic.exams.base import ExamBase
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.exam import ExamGrade
from models.student import Student
from schemas.exam import ExamGradeCreate, ExamGradeResponse, ExamGradeUpdate

router = APIRouter()


@router.post("/", response_model=ResponseSchema[ExamGradeResponse])
async def create_grade(
    grade: ExamGradeCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建考试成绩"""
    # 检查考试是否存在
    exam = db.query(ExamBase).filter(ExamBase.id == grade.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # 检查学生是否存在
    student = db.query(Student).filter(Student.id == grade.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 检查是否已存在成绩
    existing_grade = (
        db.query(ExamGrade)
        .filter(
            ExamGrade.exam_id == grade.exam_id,
            ExamGrade.student_id == grade.student_id,
            ExamGrade.is_delete == False,
        )
        .first()
    )
    if existing_grade:
        raise HTTPException(status_code=400, detail="Grade already exists")

    db_grade = ExamGrade(
        **grade.dict(),
        grader_id=current_user,
        grade_time=datetime.now(),
        status="completed",
        create_by=current_user,
    )
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return success(data=db_grade)


@router.get("/{grade_id}", response_model=ResponseSchema[ExamGradeResponse])
async def get_grade(
    grade_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考试成绩详情"""
    grade = db.query(ExamGrade).filter(ExamGrade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return success(data=grade)


@router.put("/{grade_id}", response_model=ResponseSchema[ExamGradeResponse])
async def update_grade(
    grade_id: int,
    grade_update: ExamGradeUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新考试成绩"""
    grade = db.query(ExamGrade).filter(ExamGrade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    for field, value in grade_update.dict(exclude_unset=True).items():
        setattr(grade, field, value)

    grade.update_by = current_user
    grade.update_time = datetime.now()
    grade.grader_id = current_user
    grade.grade_time = datetime.now()

    db.add(grade)
    db.commit()
    db.refresh(grade)
    return success(data=grade)


@router.delete("/{grade_id}", response_model=ResponseSchema)
async def delete_grade(
    grade_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除考试成绩"""
    grade = db.query(ExamGrade).filter(ExamGrade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    grade.is_delete = True
    grade.delete_by = current_user
    grade.delete_time = datetime.now()

    db.add(grade)
    db.commit()
    return success(message="Grade deleted successfully")


@router.get("/", response_model=ResponseSchema[List[ExamGradeResponse]])
async def list_grades(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    exam_id: Optional[int] = None,
    student_id: Optional[int] = None,
    grader_id: Optional[int] = None,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考试成绩列表"""
    query = db.query(ExamGrade).filter(ExamGrade.is_delete == False)

    if exam_id:
        query = query.filter(ExamGrade.exam_id == exam_id)
    if student_id:
        query = query.filter(ExamGrade.student_id == student_id)
    if grader_id:
        query = query.filter(ExamGrade.grader_id == grader_id)
    if status:
        query = query.filter(ExamGrade.status == status)
    if min_score is not None:
        query = query.filter(ExamGrade.score >= min_score)
    if max_score is not None:
        query = query.filter(ExamGrade.score <= max_score)

    total = query.count()
    grades = query.offset(skip).limit(limit).all()

    return success(data=grades, meta={"total": total, "skip": skip, "limit": limit})


@router.get("/stats/{exam_id}", response_model=ResponseSchema)
async def get_exam_stats(
    exam_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考试统计信息"""
    # 检查考试是否存在
    exam = db.query(ExamBase).filter(ExamBase.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # 查询成绩统计
    grades = (
        db.query(ExamGrade)
        .filter(
            ExamGrade.exam_id == exam_id,
            ExamGrade.is_delete == False,
            ExamGrade.status == "completed",
        )
        .all()
    )

    if not grades:
        return success(
            data={
                "total_students": 0,
                "graded_count": 0,
                "pass_count": 0,
                "fail_count": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "average_score": 0,
                "pass_rate": 0,
            }
        )

    scores = [grade.score for grade in grades]
    pass_count = len([score for score in scores if score >= exam.pass_score])

    stats = {
        "total_students": len(grades),
        "graded_count": len(grades),
        "pass_count": pass_count,
        "fail_count": len(grades) - pass_count,
        "highest_score": max(scores),
        "lowest_score": min(scores),
        "average_score": sum(scores) / len(scores),
        "pass_rate": (pass_count / len(grades)) * 100,
    }

    return success(data=stats)


@router.post("/batch", response_model=ResponseSchema)
async def batch_create_grades(
    grades: List[ExamGradeCreate],
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """批量创建考试成绩"""
    results = []
    errors = []

    for grade in grades:
        try:
            # 检查考试是否存在
            exam = db.query(ExamBase).filter(ExamBase.id == grade.exam_id).first()
            if not exam:
                errors.append({"grade": grade, "error": "Exam not found"})
                continue

            # 检查学生是否存在
            student = db.query(Student).filter(Student.id == grade.student_id).first()
            if not student:
                errors.append({"grade": grade, "error": "Student not found"})
                continue

            # 检查是否已存在成绩
            existing_grade = (
                db.query(ExamGrade)
                .filter(
                    ExamGrade.exam_id == grade.exam_id,
                    ExamGrade.student_id == grade.student_id,
                    ExamGrade.is_delete == False,
                )
                .first()
            )
            if existing_grade:
                errors.append({"grade": grade, "error": "Grade already exists"})
                continue

            db_grade = ExamGrade(
                **grade.dict(),
                grader_id=current_user,
                grade_time=datetime.now(),
                status="completed",
                create_by=current_user,
            )
            db.add(db_grade)
            results.append(db_grade)

        except Exception as e:
            errors.append({"grade": grade, "error": str(e)})

    if results:
        db.commit()
        for grade in results:
            db.refresh(grade)

    return success(
        data={
            "success_count": len(results),
            "error_count": len(errors),
            "errors": errors,
        }
    )
