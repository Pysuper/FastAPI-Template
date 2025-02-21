from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.course import Course
from models.evaluation import EvaluationIndicator, EvaluationRecord
from models.tasks import EvaluationTask
from models.teacher import Teacher
from schemas.tasks import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()


@router.post("/", response_model=ResponseSchema[TaskResponse])
async def create_task(
    task: TaskCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建评价任务"""
    # 检查评价指标是否都存在且启用
    for indicator_id in task.indicator_ids:
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

    # 检查评价对象是否存在
    if task.target_type == "teacher":
        target = db.query(Teacher).filter(Teacher.id == task.target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Teacher not found")
    elif task.target_type == "course":
        target = db.query(Course).filter(Course.id == task.target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Course not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid target type")

    db_task = EvaluationTask(**task.dict(), create_by=current_user)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return success(data=db_task)


@router.get("/{task_id}", response_model=ResponseSchema[TaskResponse])
async def get_task(
    task_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取评价任务详情"""
    task = (
        db.query(EvaluationTask)
        .filter(
            EvaluationTask.id == task_id,
            EvaluationTask.is_delete == False,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return success(data=task)


@router.put("/{task_id}", response_model=ResponseSchema[TaskResponse])
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新评价任务"""
    task = (
        db.query(EvaluationTask)
        .filter(
            EvaluationTask.id == task_id,
            EvaluationTask.is_delete == False,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 如果更新了评价指标，检查是否都存在且启用
    if task_update.indicator_ids:
        for indicator_id in task_update.indicator_ids:
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

    # 如果更新了评价对象，检查是否存在
    if task_update.target_type or task_update.target_id:
        target_type = task_update.target_type or task.target_type
        target_id = task_update.target_id or task.target_id

        if target_type == "teacher":
            target = db.query(Teacher).filter(Teacher.id == target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Teacher not found")
        elif target_type == "course":
            target = db.query(Course).filter(Course.id == target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Course not found")
        else:
            raise HTTPException(status_code=400, detail="Invalid target type")

    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)

    task.update_by = current_user
    task.update_time = datetime.now()

    db.add(task)
    db.commit()
    db.refresh(task)
    return success(data=task)


@router.delete("/{task_id}", response_model=ResponseSchema)
async def delete_task(
    task_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除评价任务"""
    task = (
        db.query(EvaluationTask)
        .filter(
            EvaluationTask.id == task_id,
            EvaluationTask.is_delete == False,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 检查是否已有评价记录
    if (
        db.query(EvaluationRecord)
        .filter(EvaluationRecord.task_id == task_id, EvaluationRecord.is_delete == False)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Cannot delete task with evaluation records")

    task.is_delete = True
    task.delete_by = current_user
    task.delete_time = datetime.now()

    db.add(task)
    db.commit()
    return success(message="Task deleted successfully")


@router.get("/", response_model=ResponseSchema[List[TaskResponse]])
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    evaluator_type: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取评价任务列表"""
    query = db.query(EvaluationTask).filter(EvaluationTask.is_delete == False)

    if category:
        query = query.filter(EvaluationTask.category == category)
    if target_type:
        query = query.filter(EvaluationTask.target_type == target_type)
    if target_id:
        query = query.filter(EvaluationTask.target_id == target_id)
    if evaluator_type:
        query = query.filter(EvaluationTask.evaluator_type == evaluator_type)
    if status:
        query = query.filter(EvaluationTask.status == status)
    if start_time:
        query = query.filter(EvaluationTask.start_time >= start_time)
    if end_time:
        query = query.filter(EvaluationTask.end_time <= end_time)

    total = query.count()
    tasks = query.offset(skip).limit(limit).all()

    return success(data=tasks, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{task_id}/publish", response_model=ResponseSchema[TaskResponse])
async def publish_task(
    task_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """发布评价任务"""
    task = (
        db.query(EvaluationTask)
        .filter(
            EvaluationTask.id == task_id,
            EvaluationTask.is_delete == False,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "draft":
        raise HTTPException(status_code=400, detail="Task can only be published from draft status")

    task.status = "published"
    task.update_by = current_user
    task.update_time = datetime.now()

    db.add(task)
    db.commit()
    db.refresh(task)
    return success(data=task)


@router.put("/{task_id}/close", response_model=ResponseSchema[TaskResponse])
async def close_task(
    task_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """关闭评价任务"""
    task = (
        db.query(EvaluationTask)
        .filter(
            EvaluationTask.id == task_id,
            EvaluationTask.is_delete == False,
        )
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in ["published", "ongoing"]:
        raise HTTPException(status_code=400, detail="Task can only be closed from published or ongoing status")

    task.status = "ended"
    task.update_by = current_user
    task.update_time = datetime.now()

    db.add(task)
    db.commit()
    db.refresh(task)
    return success(data=task)
