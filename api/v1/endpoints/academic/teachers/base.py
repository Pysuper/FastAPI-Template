from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, func, or_
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.department import Department
from models.teacher import Teacher
from schemas.teacher import TeacherResponse, TeacherCreate, TeacherUpdate

# 路由
router = APIRouter()


@router.post("/", response_model=ResponseSchema[TeacherResponse])
async def create_teacher(
    teacher: TeacherCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建教师"""
    # 检查工号是否已存在
    if (
        db.query(Teacher)
        .filter(
            Teacher.teacher_id == teacher.teacher_id,
            Teacher.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Teacher ID already exists")

    # 检查身份证号是否已存在
    if (
        db.query(Teacher)
        .filter(
            Teacher.id_card == teacher.id_card,
            Teacher.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="ID card already exists")

    # 检查院系是否存在
    if not db.query(Department).filter(Department.id == teacher.department_id).first():
        raise HTTPException(status_code=404, detail="Department not found")

    db_teacher = Teacher(**teacher.dict(), create_by=current_user)
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return success(data=db_teacher)


@router.get("/{teacher_id}", response_model=ResponseSchema[TeacherResponse])
async def get_teacher(
    teacher_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取教师详情"""
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id,
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return success(data=teacher)


@router.put("/{teacher_id}", response_model=ResponseSchema[TeacherResponse])
async def update_teacher(
    teacher_id: int,
    teacher_update: TeacherUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新教师信息"""
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id,
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # 如果更新院系，检查是否存在
    if teacher_update.department_id:
        if (
            not db.query(Department)
            .filter(
                Department.id == teacher_update.department_id,
            )
            .first()
        ):
            raise HTTPException(status_code=404, detail="Department not found")

    for field, value in teacher_update.dict(exclude_unset=True).items():
        setattr(teacher, field, value)

    teacher.update_by = current_user
    teacher.update_time = datetime.now()

    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return success(data=teacher)


@router.delete("/{teacher_id}", response_model=ResponseSchema)
async def delete_teacher(
    teacher_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除教师"""
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id,
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    teacher.is_delete = True
    teacher.delete_by = current_user
    teacher.delete_time = datetime.now()

    db.add(teacher)
    db.commit()
    return success(message="Teacher deleted successfully")


@router.get("/", response_model=ResponseSchema[List[TeacherResponse]])
async def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    department_id: Optional[int] = None,
    title: Optional[str] = None,
    position: Optional[str] = None,
    status: Optional[str] = None,
    is_full_time: Optional[bool] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取教师列表"""
    query = db.query(Teacher).filter(Teacher.is_delete == False)

    if keyword:
        query = query.filter(
            or_(
                Teacher.teacher_id.ilike(f"%{keyword}%"),
                Teacher.name.ilike(f"%{keyword}%"),
                Teacher.id_card.ilike(f"%{keyword}%"),
                Teacher.phone.ilike(f"%{keyword}%"),
            )
        )
    if department_id:
        query = query.filter(Teacher.department_id == department_id)
    if title:
        query = query.filter(Teacher.title == title)
    if position:
        query = query.filter(Teacher.position == position)
    if status:
        query = query.filter(Teacher.status == status)
    if is_full_time is not None:
        query = query.filter(Teacher.is_full_time == is_full_time)

    total = query.count()
    teachers = query.offset(skip).limit(limit).all()

    return success(data=teachers, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{teacher_id}/status", response_model=ResponseSchema[TeacherResponse])
async def update_teacher_status(
    teacher_id: int,
    status: str,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新教师状态"""
    teacher = (
        db.query(Teacher)
        .filter(
            Teacher.id == teacher_id,
            Teacher.is_delete == False,
        )
        .first()
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    valid_statuses = ["active", "retired", "resigned"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    teacher.status = status
    teacher.update_by = current_user
    teacher.update_time = datetime.now()

    # 如果是离职状态，设置离职日期
    if status in ["retired", "resigned"] and not teacher.leave_date:
        teacher.leave_date = datetime.now()

    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return success(data=teacher)


@router.get("/stats", response_model=ResponseSchema)
async def get_teacher_stats(
    department_id: Optional[int] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取教师统计信息"""
    query = db.query(Teacher).filter(Teacher.is_delete == False)

    if department_id:
        query = query.filter(Teacher.department_id == department_id)

    total_teachers = query.count()
    active_teachers = query.filter(Teacher.status == "active").count()
    retired_teachers = query.filter(Teacher.status == "retired").count()
    resigned_teachers = query.filter(Teacher.status == "resigned").count()
    full_time_teachers = query.filter(Teacher.is_full_time == True).count()
    part_time_teachers = query.filter(Teacher.is_full_time == False).count()

    # 性别分布
    gender_distribution = {
        gender: count
        for gender, count in db.query(Teacher.gender, func.count(Teacher.id))
        .filter(Teacher.is_delete == False)
        .group_by(Teacher.gender)
        .all()
    }

    # 职称分布
    title_distribution = {
        title: count
        for title, count in db.query(Teacher.title, func.count(Teacher.id))
        .filter(Teacher.is_delete == False)
        .group_by(Teacher.title)
        .all()
    }

    # 学历分布
    education_distribution = {
        education: count
        for education, count in db.query(Teacher.education, func.count(Teacher.id))
        .filter(Teacher.is_delete == False)
        .group_by(Teacher.education)
        .all()
    }

    # 年龄分布
    age_ranges = [(0, 30), (30, 40), (40, 50), (50, 60), (60, 100)]
    age_distribution = {}
    for start, end in age_ranges:
        count = query.filter(
            extract("year", func.current_date()) - extract("year", Teacher.birth_date) >= start,
            extract("year", func.current_date()) - extract("year", Teacher.birth_date) < end,
        ).count()
        age_distribution[f"{start}-{end}"] = count

    stats = {
        "total_teachers": total_teachers,
        "active_teachers": active_teachers,
        "retired_teachers": retired_teachers,
        "resigned_teachers": resigned_teachers,
        "full_time_teachers": full_time_teachers,
        "part_time_teachers": part_time_teachers,
        "gender_distribution": gender_distribution,
        "title_distribution": title_distribution,
        "education_distribution": education_distribution,
        "age_distribution": age_distribution,
    }

    return success(data=stats)
