from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.v1.endpoints.academic.evaluations.tasks import EvaluationTask
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.evaluation import EvaluationIndicator, EvaluationRecord
from models.student import Student
from models.teacher import Teacher
from schemas.record import RecordCreate, RecordResponse, RecordUpdate

router = APIRouter()


@router.post("/", response_model=ResponseSchema[RecordResponse])
async def create_record(
    record: RecordCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建评价记录"""
    # 检查评价任务是否存在且在进行中
    task = (
        db.query(EvaluationTask)
        .filter(
            EvaluationTask.id == record.task_id,
            EvaluationTask.is_delete == False,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in ["published", "ongoing"]:
        raise HTTPException(status_code=400, detail="Task is not available for evaluation")

    # 检查是否已提交过评价
    existing_record = (
        db.query(EvaluationRecord)
        .filter(
            EvaluationRecord.task_id == record.task_id,
            EvaluationRecord.evaluator_id == current_user,
            EvaluationRecord.is_delete == False,
        )
        .first()
    )
    if existing_record:
        raise HTTPException(status_code=400, detail="You have already submitted evaluation for this task")

    # 检查评分指标是否正确
    for indicator_id in record.scores.keys():
        if indicator_id not in task.indicator_ids:
            raise HTTPException(status_code=400, detail=f"Invalid indicator: {indicator_id}")
        indicator = (
            db.query(EvaluationIndicator)
            .filter(
                EvaluationIndicator.id == indicator_id,
                EvaluationIndicator.is_delete == False,
                EvaluationIndicator.is_active == True,
            )
            .first()
        )
        if not indicator:
            raise HTTPException(status_code=400, detail=f"Invalid or inactive indicator: {indicator_id}")
        score = record.scores[indicator_id]
        if score < indicator.min_score or score > indicator.max_score:
            raise HTTPException(
                status_code=400,
                detail=f"Score for indicator {indicator_id} must be between {indicator.min_score} and {indicator.max_score}",
            )

    # 计算总分
    indicators = {
        ind.id: ind
        for ind in db.query(EvaluationIndicator).filter(EvaluationIndicator.id.in_(task.indicator_ids)).all()
    }
    total_score = sum(record.scores[ind_id] * indicators[ind_id].weight for ind_id in record.scores.keys())

    # 获取评价人类型
    evaluator_type = None
    if task.evaluator_type == "student":
        if db.query(Student).filter(Student.id == current_user).first():
            evaluator_type = "student"
    elif task.evaluator_type == "teacher":
        if db.query(Teacher).filter(Teacher.id == current_user).first():
            evaluator_type = "teacher"
    elif task.evaluator_type == "expert":
        if db.query(Expert).filter(Expert.id == current_user).first():
            evaluator_type = "expert"

    if not evaluator_type:
        raise HTTPException(status_code=403, detail="You are not allowed to evaluate this task")

    db_record = EvaluationRecord(
        task_id=record.task_id,
        evaluator_id=current_user,
        evaluator_type=evaluator_type,
        scores=record.scores,
        total_score=total_score,
        comments=record.comments,
        create_by=current_user,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return success(data=db_record)


@router.get("/{record_id}", response_model=ResponseSchema[RecordResponse])
async def get_record(record_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取评价记录详情"""
    record = (
        db.query(EvaluationRecord).filter(EvaluationRecord.id == record_id, EvaluationRecord.is_delete == False).first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # 检查访问权限
    task = db.query(EvaluationTask).filter(EvaluationTask.id == record.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 只有评价人自己和管理员可以查看详情
    if record.evaluator_id != current_user and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    return success(data=record)


@router.put("/{record_id}", response_model=ResponseSchema[RecordResponse])
async def update_record(
    record_id: int,
    record_update: RecordUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新评价记录"""
    record = (
        db.query(EvaluationRecord).filter(EvaluationRecord.id == record_id, EvaluationRecord.is_delete == False).first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # 检查访问权限
    task = db.query(EvaluationTask).filter(EvaluationTask.id == record.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 只有评价人自己可以修改评价内容
    if record.evaluator_id != current_user:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 只能修改未审核的评价
    if record.status != "submitted":
        raise HTTPException(status_code=400, detail="Cannot update approved or rejected record")

    # 如果更新了评分，需要重新验证和计算总分
    if record_update.scores:
        # 检查评分指标是否正确
        for indicator_id in record_update.scores.keys():
            if indicator_id not in task.indicator_ids:
                raise HTTPException(status_code=400, detail=f"Invalid indicator: {indicator_id}")
            indicator = (
                db.query(EvaluationIndicator)
                .filter(
                    EvaluationIndicator.id == indicator_id,
                    EvaluationIndicator.is_delete == False,
                    EvaluationIndicator.is_active == True,
                )
                .first()
            )
            if not indicator:
                raise HTTPException(status_code=400, detail=f"Invalid or inactive indicator: {indicator_id}")
            score = record_update.scores[indicator_id]
            if score < indicator.min_score or score > indicator.max_score:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score for indicator {indicator_id} must be between {indicator.min_score} and {indicator.max_score}",
                )

        # 计算新的总分
        indicators = {
            ind.id: ind
            for ind in db.query(EvaluationIndicator).filter(EvaluationIndicator.id.in_(task.indicator_ids)).all()
        }
        record_update.total_score = sum(
            record_update.scores[ind_id] * indicators[ind_id].weight for ind_id in record_update.scores.keys()
        )

    for field, value in record_update.dict(exclude_unset=True).items():
        setattr(record, field, value)

    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.delete("/{record_id}", response_model=ResponseSchema)
async def delete_record(record_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """删除评价记录"""
    record = (
        db.query(EvaluationRecord).filter(EvaluationRecord.id == record_id, EvaluationRecord.is_delete == False).first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # 检查访问权限
    task = db.query(EvaluationTask).filter(EvaluationTask.id == record.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 只有评价人自己和管理员可以删除评价
    if record.evaluator_id != current_user and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    # 只能删除未审核的评价
    if record.status != "submitted":
        raise HTTPException(status_code=400, detail="Cannot delete approved or rejected record")

    record.is_delete = True
    record.delete_by = current_user
    record.delete_time = datetime.now()

    db.add(record)
    db.commit()
    return success(message="Record deleted successfully")


@router.get("/", response_model=ResponseSchema[List[RecordResponse]])
async def list_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    task_id: Optional[int] = None,
    evaluator_id: Optional[int] = None,
    evaluator_type: Optional[str] = None,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取评价记录列表"""
    query = db.query(EvaluationRecord).filter(EvaluationRecord.is_delete == False)

    # 非管理员只能查看自己的评价记录
    if not is_admin(current_user):
        query = query.filter(EvaluationRecord.evaluator_id == current_user)
    else:
        if evaluator_id:
            query = query.filter(EvaluationRecord.evaluator_id == evaluator_id)

    if task_id:
        query = query.filter(EvaluationRecord.task_id == task_id)
    if evaluator_type:
        query = query.filter(EvaluationRecord.evaluator_type == evaluator_type)
    if status:
        query = query.filter(EvaluationRecord.status == status)
    if min_score is not None:
        query = query.filter(EvaluationRecord.total_score >= min_score)
    if max_score is not None:
        query = query.filter(EvaluationRecord.total_score <= max_score)

    total = query.count()
    records = query.offset(skip).limit(limit).all()

    return success(data=records, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{record_id}/approve", response_model=ResponseSchema[RecordResponse])
async def approve_record(
    record_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """审核通过评价记录"""
    # 检查是否是管理员
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    record = (
        db.query(EvaluationRecord).filter(EvaluationRecord.id == record_id, EvaluationRecord.is_delete == False).first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if record.status != "submitted":
        raise HTTPException(status_code=400, detail="Record is not in submitted status")

    record.status = "approved"
    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.put("/{record_id}/reject", response_model=ResponseSchema[RecordResponse])
async def reject_record(record_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """驳回评价记录"""
    # 检查是否是管理员
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    record = (
        db.query(EvaluationRecord).filter(EvaluationRecord.id == record_id, EvaluationRecord.is_delete == False).first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if record.status != "submitted":
        raise HTTPException(status_code=400, detail="Record is not in submitted status")

    record.status = "rejected"
    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.get("/stats/{task_id}", response_model=ResponseSchema)
async def get_task_stats(task_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取评价任务统计信息"""
    task = db.query(EvaluationTask).filter(EvaluationTask.id == task_id, EvaluationTask.is_delete == False).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 获取所有已审核的评价记录
    records = (
        db.query(EvaluationRecord)
        .filter(
            EvaluationRecord.task_id == task_id,
            EvaluationRecord.status == "approved",
            EvaluationRecord.is_delete == False,
        )
        .all()
    )

    if not records:
        return success(
            data={
                "total_records": 0,
                "approved_count": 0,
                "rejected_count": 0,
                "average_score": 0,
                "max_score": 0,
                "min_score": 0,
                "score_distribution": {},
                "indicator_stats": {},
            }
        )

    # 统计基本信息
    total_records = (
        db.query(EvaluationRecord)
        .filter(EvaluationRecord.task_id == task_id, EvaluationRecord.is_delete == False)
        .count()
    )
    approved_count = len(records)
    rejected_count = (
        db.query(EvaluationRecord)
        .filter(
            EvaluationRecord.task_id == task_id,
            EvaluationRecord.status == "rejected",
            EvaluationRecord.is_delete == False,
        )
        .count()
    )

    # 分数统计
    scores = [record.total_score for record in records]
    average_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)

    # 分数分布
    score_ranges = [(0, 60), (60, 70), (70, 80), (80, 90), (90, 100)]
    score_distribution = {f"{start}-{end}": len([s for s in scores if start <= s < end]) for start, end in score_ranges}

    # 指标统计
    indicator_stats = {}
    for indicator_id in task.indicator_ids:
        indicator_scores = [record.scores.get(str(indicator_id)) for record in records]
        indicator_scores = [s for s in indicator_scores if s is not None]
        if indicator_scores:
            indicator_stats[indicator_id] = {
                "average": sum(indicator_scores) / len(indicator_scores),
                "max": max(indicator_scores),
                "min": min(indicator_scores),
            }

    stats = {
        "total_records": total_records,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "average_score": average_score,
        "max_score": max_score,
        "min_score": min_score,
        "score_distribution": score_distribution,
        "indicator_stats": indicator_stats,
    }

    return success(data=stats)
