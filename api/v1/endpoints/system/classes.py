# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：classes.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：Speedy classes.py
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_active_user
from core.dependencies import async_db
from core.dependencies.pagination import get_pagination_params
from schemas.base.pagination import PaginatedResponse, PaginationParams
from schemas.class_ import ClassResponse, ClassCreate, ClassUpdate
from services.academic.organization.class_ import ClassService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ClassResponse])
async def get_classes(
    *,
    db: Session = Depends(async_db),
    pagination: PaginationParams = Depends(get_pagination_params),
    major_id: int = None,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    获取班级列表
    """
    class_service = ClassService(db)
    classes = class_service.get_classes(
        skip=(pagination.page - 1) * pagination.size, limit=pagination.size, major_id=major_id
    )
    total = class_service.count_classes(major_id=major_id)
    return {
        "data": classes,
        "total": total,
        "page": pagination.page,
        "size": pagination.size,
        "pages": (total + pagination.size - 1) // pagination.size,
    }


@router.post("/", response_model=ClassResponse)
async def create_class(
    *,
    db: Session = Depends(async_db),
    class_in: ClassCreate,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    创建班级
    """
    class_service = ClassService(db)
    # 检查专业是否存在
    if not class_service.major_exists(class_in.major_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专业不存在")
    # 检查班级名称是否已存在
    class_ = class_service.get_class_by_name(name=class_in.name, major_id=class_in.major_id)
    if class_:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该专业下已存在同名班级")
    class_ = class_service.create_class(class_in)
    return class_


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: int,
    db: Session = Depends(async_db),
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    获取班级信息
    """
    class_service = ClassService(db)
    class_ = class_service.get_class(class_id)
    if not class_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="班级不存在")
    return class_


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    *,
    db: Session = Depends(async_db),
    class_id: int,
    class_in: ClassUpdate,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    更新班级信息
    """
    class_service = ClassService(db)
    class_ = class_service.get_class(class_id)
    if not class_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="班级不存在")
    # 如果更新了专业，检查新专业是否存��
    if class_in.major_id and class_in.major_id != class_.major_id:
        if not class_service.major_exists(class_in.major_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专业不存在")
    class_ = class_service.update_class(class_, class_in)
    return class_


@router.delete("/{class_id}")
async def delete_class(
    *,
    db: Session = Depends(async_db),
    class_id: int,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    删除班级
    """
    class_service = ClassService(db)
    class_ = class_service.get_class(class_id)
    if not class_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="班级不存在")
    # 检查是否有关联的学生
    if class_service.has_related_students(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该班级下还有学生，无法删除")
    class_service.delete_class(class_id)
    return {"msg": "删除成功"}
