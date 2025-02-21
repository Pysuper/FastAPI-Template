from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from models.evaluation import EvaluationIndicator
from schemas.evaluation import IndicatorCreate, IndicatorResponse, IndicatorUpdate

# 路由
router = APIRouter()


@router.post("/", response_model=ResponseSchema[IndicatorResponse])
async def create_indicator(
    indicator: IndicatorCreate, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """创建评价指标"""
    # 检查编码是否已存在
    if (
        db.query(EvaluationIndicator)
        .filter(EvaluationIndicator.code == indicator.code, EvaluationIndicator.is_delete == False)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Indicator code already exists")

    # 如果有父级指标，检查是否存在
    if indicator.parent_id:
        parent = (
            db.query(EvaluationIndicator)
            .filter(EvaluationIndicator.id == indicator.parent_id, EvaluationIndicator.is_delete == False)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent indicator not found")
        # 设置正确的层级
        indicator.level = parent.level + 1

    db_indicator = EvaluationIndicator(**indicator.dict(), create_by=current_user)
    db.add(db_indicator)
    db.commit()
    db.refresh(db_indicator)
    return success(data=db_indicator)


@router.get("/{indicator_id}", response_model=ResponseSchema[IndicatorResponse])
async def get_indicator(
    indicator_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """获取评价指标详情"""
    indicator = (
        db.query(EvaluationIndicator)
        .filter(EvaluationIndicator.id == indicator_id, EvaluationIndicator.is_delete == False)
        .first()
    )
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return success(data=indicator)


@router.put("/{indicator_id}", response_model=ResponseSchema[IndicatorResponse])
async def update_indicator(
    indicator_id: int,
    indicator_update: IndicatorUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新评价指标"""
    indicator = (
        db.query(EvaluationIndicator)
        .filter(EvaluationIndicator.id == indicator_id, EvaluationIndicator.is_delete == False)
        .first()
    )
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    # 检查编码是否已存在
    if indicator_update.code and indicator_update.code != indicator.code:
        if (
            db.query(EvaluationIndicator)
            .filter(
                EvaluationIndicator.code == indicator_update.code,
                EvaluationIndicator.id != indicator_id,
                EvaluationIndicator.is_delete == False,
            )
            .first()
        ):
            raise HTTPException(status_code=400, detail="Indicator code already exists")

    # 如果更新父级指标，检查是否存在并更新层级
    if indicator_update.parent_id is not None:
        if indicator_update.parent_id > 0:
            parent = (
                db.query(EvaluationIndicator)
                .filter(EvaluationIndicator.id == indicator_update.parent_id, EvaluationIndicator.is_delete == False)
                .first()
            )
            if not parent:
                raise HTTPException(status_code=404, detail="Parent indicator not found")
            indicator_update.level = parent.level + 1
        else:
            indicator_update.level = 1

    for field, value in indicator_update.dict(exclude_unset=True).items():
        setattr(indicator, field, value)

    indicator.update_by = current_user
    indicator.update_time = datetime.now()

    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return success(data=indicator)


@router.delete("/{indicator_id}", response_model=ResponseSchema)
async def delete_indicator(
    indicator_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """删除��价指标"""
    indicator = (
        db.query(EvaluationIndicator)
        .filter(EvaluationIndicator.id == indicator_id, EvaluationIndicator.is_delete == False)
        .first()
    )
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    # 检查是否有子指标
    if (
        db.query(EvaluationIndicator)
        .filter(EvaluationIndicator.parent_id == indicator_id, EvaluationIndicator.is_delete == False)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Cannot delete indicator with children")

    indicator.is_delete = True
    indicator.delete_by = current_user
    indicator.delete_time = datetime.now()

    db.add(indicator)
    db.commit()
    return success(message="Indicator deleted successfully")


@router.get("/", response_model=ResponseSchema[List[IndicatorResponse]])
async def list_indicators(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    parent_id: Optional[int] = None,
    level: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取评价指标列表"""
    query = db.query(EvaluationIndicator).filter(EvaluationIndicator.is_delete == False)

    if category:
        query = query.filter(EvaluationIndicator.category == category)
    if parent_id is not None:
        query = query.filter(EvaluationIndicator.parent_id == parent_id)
    if level:
        query = query.filter(EvaluationIndicator.level == level)
    if is_active is not None:
        query = query.filter(EvaluationIndicator.is_active == is_active)

    # 按层级和排序字段排序
    query = query.order_by(EvaluationIndicator.level, EvaluationIndicator.sort)

    total = query.count()
    indicators = query.offset(skip).limit(limit).all()

    return success(data=indicators, meta={"total": total, "skip": skip, "limit": limit})


@router.get("/tree", response_model=ResponseSchema)
async def get_indicator_tree(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取评价指标树形结构"""
    query = db.query(EvaluationIndicator).filter(EvaluationIndicator.is_delete == False)

    if category:
        query = query.filter(EvaluationIndicator.category == category)
    if is_active is not None:
        query = query.filter(EvaluationIndicator.is_active == is_active)

    # ���取所有指标并按层级排序
    indicators = query.order_by(EvaluationIndicator.level, EvaluationIndicator.sort).all()

    # 构建树形结构
    def build_tree(parent_id: Optional[int] = None) -> List[dict]:
        nodes = []
        children = [ind for ind in indicators if ind.parent_id == parent_id]
        for child in children:
            node = {
                "id": child.id,
                "name": child.name,
                "code": child.code,
                "category": child.category,
                "weight": child.weight,
                "max_score": child.max_score,
                "min_score": child.min_score,
                "description": child.description,
                "level": child.level,
                "sort": child.sort,
                "is_active": child.is_active,
                "children": build_tree(child.id),
            }
            nodes.append(node)
        return nodes

    tree = build_tree(None)
    return success(data=tree)
