from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.department import Classes, Department, Major
from models.student import Student, StudentStatus
from schemas.student import StatusRecordCreate, StatusRecordResponse, StatusRecordUpdate

router = APIRouter()


@router.post("/", response_model=ResponseSchema[StatusRecordResponse])
async def create_status_record(
    record: StatusRecordCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建学籍变动记录"""
    # 检查学生是否存在
    student = db.query(Student).filter(Student.id == record.student_id, Student.is_delete == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 检查变动类型是否有效
    valid_types = ["enrollment", "transfer", "suspension", "resumption", "graduation", "dropout"]
    if record.change_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid change type. Must be one of: {', '.join(valid_types)}")

    # 检查院系和专业是否存在
    if record.target_department_id:
        if not db.query(Department).filter(Department.id == record.target_department_id).first():
            raise HTTPException(status_code=404, detail="Target department not found")
    if record.target_major_id:
        if not db.query(Major).filter(Major.id == record.target_major_id).first():
            raise HTTPException(status_code=404, detail="Target major not found")
    if record.target_class_id:
        if not db.query(Classes).filter(Classes.id == record.target_class_id).first():
            raise HTTPException(status_code=404, detail="Target class not found")

    # 设置原始院系和专业
    record.original_department_id = student.department_id
    record.original_major_id = student.major_id
    record.original_class_id = student.class_id

    db_record = StudentStatus(**record.dict(), create_by=current_user)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return success(data=db_record)


@router.get("/{record_id}", response_model=ResponseSchema[StatusRecordResponse])
async def get_status_record(
    record_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取学籍变动记录详情"""
    record = (
        db.query(StudentStatus)
        .filter(
            StudentStatus.id == record_id,
            StudentStatus.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Status record not found")
    return success(data=record)


@router.put("/{record_id}", response_model=ResponseSchema[StatusRecordResponse])
async def update_status_record(
    record_id: int,
    record_update: StatusRecordUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新学籍变动记录"""
    record = (
        db.query(StudentStatus)
        .filter(
            StudentStatus.id == record_id,
            StudentStatus.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Status record not found")

    # 只能更新待审核的记录
    if record.status != "pending":
        raise HTTPException(status_code=400, detail="Can only update pending records")

    for field, value in record_update.dict(exclude_unset=True).items():
        setattr(record, field, value)

    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.delete("/{record_id}", response_model=ResponseSchema)
async def delete_status_record(
    record_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除学籍变动记录"""
    record = (
        db.query(StudentStatus)
        .filter(
            StudentStatus.id == record_id,
            StudentStatus.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Status record not found")

    # 只能删除待审核的记录
    if record.status != "pending":
        raise HTTPException(status_code=400, detail="Can only delete pending records")

    record.is_delete = True
    record.delete_by = current_user
    record.delete_time = datetime.now()

    db.add(record)
    db.commit()
    return success(message="Status record deleted successfully")


@router.get("/", response_model=ResponseSchema[List[StatusRecordResponse]])
async def list_status_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    student_id: Optional[int] = None,
    change_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取学籍变动记录列表"""
    query = db.query(StudentStatus).filter(StudentStatus.is_delete == False)

    if student_id:
        query = query.filter(StudentStatus.student_id == student_id)
    if change_type:
        query = query.filter(StudentStatus.change_type == change_type)
    if status:
        query = query.filter(StudentStatus.status == status)
    if start_date:
        query = query.filter(StudentStatus.effective_date >= start_date)
    if end_date:
        query = query.filter(StudentStatus.effective_date <= end_date)

    total = query.count()
    records = query.offset(skip).limit(limit).all()

    return success(data=records, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{record_id}/approve", response_model=ResponseSchema[StatusRecordResponse])
async def approve_status_record(
    record_id: int,
    comments: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """审核通过学籍变动记录"""
    # 检查是否有审核权限
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    record = (
        db.query(StudentStatus)
        .filter(
            StudentStatus.id == record_id,
            StudentStatus.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Status record not found")

    if record.status != "pending":
        raise HTTPException(status_code=400, detail="Record is not in pending status")

    # 更新学籍变动记录状态
    record.status = "approved"
    record.approver_id = current_user
    record.approve_time = datetime.now()
    record.approve_comments = comments
    record.update_by = current_user
    record.update_time = datetime.now()

    # 更新学生信息
    student = db.query(Student).filter(Student.id == record.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if record.change_type == "transfer":
        # 转专业
        student.department_id = record.target_department_id
        student.major_id = record.target_major_id
        student.class_id = record.target_class_id
    elif record.change_type == "suspension":
        # 休学
        student.status = "suspended"
    elif record.change_type == "resumption":
        # 复学
        student.status = "active"
    elif record.change_type == "graduation":
        # 毕业
        student.status = "graduated"
        student.graduation_date = record.effective_date
    elif record.change_type == "dropout":
        # 退学
        student.status = "dropped"

    student.update_by = current_user
    student.update_time = datetime.now()

    db.add(record)
    db.add(student)
    db.commit()
    db.refresh(record)
    return success(data=record)


@router.put("/{record_id}/reject", response_model=ResponseSchema[StatusRecordResponse])
async def reject_status_record(
    record_id: int,
    comments: str,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """驳回学籍变动记录"""
    # 检查是否有审核权限
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    record = (
        db.query(StudentStatus)
        .filter(
            StudentStatus.id == record_id,
            StudentStatus.is_delete == False,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Status record not found")

    if record.status != "pending":
        raise HTTPException(status_code=400, detail="Record is not in pending status")

    record.status = "rejected"
    record.approver_id = current_user
    record.approve_time = datetime.now()
    record.approve_comments = comments
    record.update_by = current_user
    record.update_time = datetime.now()

    db.add(record)
    db.commit()
    db.refresh(record)
    return success(data=record)
