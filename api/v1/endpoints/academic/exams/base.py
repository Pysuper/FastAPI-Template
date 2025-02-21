from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from schemas.exam import ExamBase, ExamCreate, ExamResponse, ExamUpdate

router = APIRouter()


@router.post("/", response_model=ResponseSchema[ExamResponse])
async def create_exam(
    exam: ExamCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建考试"""
    db_exam = ExamBase(**exam.dict(), create_by=current_user)
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return success(data=db_exam)


@router.get("/{exam_id}", response_model=ResponseSchema[ExamResponse])
async def get_exam(
    exam_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考试详情"""
    exam = db.query(ExamBase).filter(ExamBase.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return success(data=exam)


@router.put("/{exam_id}", response_model=ResponseSchema[ExamResponse])
async def update_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新考试信息"""
    exam = db.query(ExamBase).filter(ExamBase.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    for field, value in exam_update.dict(exclude_unset=True).items():
        setattr(exam, field, value)

    exam.update_by = current_user
    exam.update_time = datetime.now()

    db.add(exam)
    db.commit()
    db.refresh(exam)
    return success(data=exam)


@router.delete("/{exam_id}", response_model=ResponseSchema)
async def delete_exam(
    exam_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除考试"""
    exam = db.query(ExamBase).filter(ExamBase.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    exam.is_delete = True
    exam.delete_by = current_user
    exam.delete_time = datetime.now()

    db.add(exam)
    db.commit()
    return success(message="Exam deleted successfully")


@router.get("/", response_model=ResponseSchema[List[ExamResponse]])
async def list_exams(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    course_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取考试列表"""
    query = db.query(ExamBase).filter(ExamBase.is_delete == False)

    if course_id:
        query = query.filter(ExamBase.course_id == course_id)
    if teacher_id:
        query = query.filter(ExamBase.teacher_id == teacher_id)
    if status:
        query = query.filter(ExamBase.status == status)

    total = query.count()
    exams = query.offset(skip).limit(limit).all()

    return success(data=exams, meta={"total": total, "skip": skip, "limit": limit})
