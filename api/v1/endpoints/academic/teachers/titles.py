from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.teacher import Teacher, TeacherTitle
from schemas.teacher import TitleResponse, TitleCreate, TitleUpdate

# 路由
router = APIRouter()


@router.post("/", response_model=ResponseSchema[TitleResponse])
async def create_title(
    title: TitleCreate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建职称记录"""
    # 检查教师是否存在
    if (
        not db.query(Teacher)
        .filter(
            Teacher.id == title.teacher_id,
            Teacher.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=404, detail="Teacher not found")

    # 检查职称级别是否有效
    valid_levels = ["professor", "associate", "lecturer", "assistant"]
    if title.level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid level. Must be one of: {', '.join(valid_levels)}",
        )

    # 检查是否已有同级别的有效职称
    if (
        db.query(TeacherTitle)
        .filter(
            TeacherTitle.teacher_id == title.teacher_id,
            TeacherTitle.level == title.level,
            TeacherTitle.status == "active",
            TeacherTitle.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Teacher already has an active {title.level} title",
        )

    db_title = TeacherTitle(**title.dict(), create_by=current_user)
    db.add(db_title)
    db.commit()
    db.refresh(db_title)
    return success(data=db_title)


@router.get("/{title_id}", response_model=ResponseSchema[TitleResponse])
async def get_title(
    title_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取职称记录详情"""
    title = (
        db.query(TeacherTitle)
        .filter(
            TeacherTitle.id == title_id,
            TeacherTitle.is_delete == False,
        )
        .first()
    )
    if not title:
        raise HTTPException(status_code=404, detail="Title record not found")
    return success(data=title)


@router.put("/{title_id}", response_model=ResponseSchema[TitleResponse])
async def update_title(
    title_id: int,
    title_update: TitleUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新职称记录"""
    title = (
        db.query(TeacherTitle)
        .filter(
            TeacherTitle.id == title_id,
            TeacherTitle.is_delete == False,
        )
        .first()
    )
    if not title:
        raise HTTPException(status_code=404, detail="Title record not found")

    # 检查职称级别是否有效
    if title_update.level:
        valid_levels = ["professor", "associate", "lecturer", "assistant"]
        if title_update.level not in valid_levels:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid level. Must be one of: {', '.join(valid_levels)}",
            )

        # 检查是否已有同级别的有效职称
        if (
            db.query(TeacherTitle)
            .filter(
                TeacherTitle.teacher_id == title.teacher_id,
                TeacherTitle.level == title_update.level,
                TeacherTitle.status == "active",
                TeacherTitle.is_delete == False,
                TeacherTitle.id != title_id,
            )
            .first()
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Teacher already has an active {title_update.level} title",
            )

    for field, value in title_update.dict(exclude_unset=True).items():
        setattr(title, field, value)

    title.update_by = current_user
    title.update_time = datetime.now()

    db.add(title)
    db.commit()
    db.refresh(title)
    return success(data=title)


@router.delete("/{title_id}", response_model=ResponseSchema)
async def delete_title(
    title_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除职称记录"""
    title = (
        db.query(TeacherTitle)
        .filter(
            TeacherTitle.id == title_id,
            TeacherTitle.is_delete == False,
        )
        .first()
    )
    if not title:
        raise HTTPException(status_code=404, detail="Title record not found")

    title.is_delete = True
    title.delete_by = current_user
    title.delete_time = datetime.now()

    db.add(title)
    db.commit()
    return success(message="Title record deleted successfully")


@router.get("/", response_model=ResponseSchema[List[TitleResponse]])
async def list_titles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    teacher_id: Optional[int] = None,
    title: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取职称记录列表"""
    query = db.query(TeacherTitle).filter(TeacherTitle.is_delete == False)

    if teacher_id:
        query = query.filter(TeacherTitle.teacher_id == teacher_id)
    if title:
        query = query.filter(TeacherTitle.title == title)
    if level:
        query = query.filter(TeacherTitle.level == level)
    if status:
        query = query.filter(TeacherTitle.status == status)
    if start_date:
        query = query.filter(TeacherTitle.issue_date >= start_date)
    if end_date:
        query = query.filter(TeacherTitle.issue_date <= end_date)

    total = query.count()
    titles = query.offset(skip).limit(limit).all()

    return success(data=titles, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{title_id}/revoke", response_model=ResponseSchema[TitleResponse])
async def revoke_title(
    title_id: int,
    reason: str,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """撤销职称"""
    title = (
        db.query(TeacherTitle)
        .filter(
            TeacherTitle.id == title_id,
            TeacherTitle.is_delete == False,
        )
        .first()
    )
    if not title:
        raise HTTPException(status_code=404, detail="Title record not found")

    if title.status != "active":
        raise HTTPException(status_code=400, detail="Can only revoke active titles")

    title.status = "revoked"
    title.revoke_reason = reason
    title.update_by = current_user
    title.update_time = datetime.now()

    db.add(title)
    db.commit()
    db.refresh(title)
    return success(data=title)


@router.get("/stats", response_model=ResponseSchema)
async def get_title_stats(
    department_id: Optional[int] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取职称统计信息"""
    query = (
        db.query(TeacherTitle)
        .join(Teacher, TeacherTitle.teacher_id == Teacher.id)
        .filter(TeacherTitle.is_delete == False, Teacher.is_delete == False)
    )

    if department_id:
        query = query.filter(Teacher.department_id == department_id)

    # 职称级别分布
    level_distribution = {
        level: count
        for level, count in db.query(TeacherTitle.level, func.count(TeacherTitle.id))
        .filter(
            TeacherTitle.status == "active",
            TeacherTitle.is_delete == False,
        )
        .group_by(TeacherTitle.level)
        .all()
    }

    # 职称状态分布
    status_distribution = {
        status: count
        for status, count in db.query(
            TeacherTitle.status,
            func.count(TeacherTitle.id),
        )
        .filter(TeacherTitle.is_delete == False)
        .group_by(TeacherTitle.status)
        .all()
    }

    # 按年份统计获得职称人数
    year_distribution = {
        year: count
        for year, count in db.query(
            extract("year", TeacherTitle.issue_date),
            func.count(TeacherTitle.id),
        )
        .filter(TeacherTitle.is_delete == False)
        .group_by(extract("year", TeacherTitle.issue_date))
        .all()
    }

    stats = {
        "level_distribution": level_distribution,
        "status_distribution": status_distribution,
        "year_distribution": year_distribution,
    }

    return success(data=stats)
