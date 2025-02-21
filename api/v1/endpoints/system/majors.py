# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：majors.py
@Author  ：PySuper
@Date    ：2024/12/20 14:43 
@Desc    ：Speedy majors.py
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_active_user
from core.dependencies import async_db
from core.dependencies.pagination import get_pagination_params
from schemas.base.pagination import PaginatedResponse, PaginationParams
from schemas.major import MajorResponse, MajorCreate, MajorUpdate
from services.academic.organization.major import MajorService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MajorResponse])
async def get_majors(
    *,
    db: Session = Depends(async_db),
    pagination: PaginationParams = Depends(get_pagination_params),
    department_id: int = None,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    获取专业列表
    """
    major_service = MajorService(db)
    majors = major_service.get_majors(
        skip=(pagination.page - 1) * pagination.size, limit=pagination.size, department_id=department_id
    )
    total = major_service.count_majors(department_id=department_id)
    return {
        "data": majors,
        "total": total,
        "page": pagination.page,
        "size": pagination.size,
        "pages": (total + pagination.size - 1) // pagination.size,
    }


@router.post("/", response_model=MajorResponse)
async def create_major(
    *,
    db: Session = Depends(async_db),
    major_in: MajorCreate,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    创建专业
    """
    major_service = MajorService(db)
    # 检查院系是否存在
    if not major_service.department_exists(major_in.department_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="院系不存在")
    # 检查专业名称是否已存在
    major = major_service.get_major_by_name(name=major_in.name, department_id=major_in.department_id)
    if major:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该院系下已存在同名专业")
    major = major_service.create_major(major_in)
    return major


@router.get("/{major_id}", response_model=MajorResponse)
async def get_major(
    major_id: int,
    db: Session = Depends(async_db),
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    获取专业信息
    """
    major_service = MajorService(db)
    major = major_service.get_major(major_id)
    if not major:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专业不存在")
    return major


@router.put("/{major_id}", response_model=MajorResponse)
async def update_major(
    *,
    db: Session = Depends(async_db),
    major_id: int,
    major_in: MajorUpdate,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    更新专业信息
    """
    major_service = MajorService(db)
    major = major_service.get_major(major_id)
    if not major:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专业不存在")
    # 如果更新了院系，检查新院系是否存在
    if major_in.department_id and major_in.department_id != major.department_id:
        if not major_service.department_exists(major_in.department_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="院系不存在")
    major = major_service.update_major(major, major_in)
    return major


@router.delete("/{major_id}")
async def delete_major(
    *,
    db: Session = Depends(async_db),
    major_id: int,
    current_user=Depends(get_current_active_user),
) -> Any:
    """
    删除专业
    """
    major_service = MajorService(db)
    major = major_service.get_major(major_id)
    if not major:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专业不存在")
    # 检查是否有关联的班级
    if major_service.has_related_classes(major_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该专业下还有班级，无法删除")
    major_service.delete_major(major_id)
    return {"msg": "删除成功"}
