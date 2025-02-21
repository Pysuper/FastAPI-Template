from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth.permissions import PermissionChecker, ResourceType, Action
from core.validators import ResourceCreate, ResourceUpdate, ResponseModel
from services.library_service import LibraryService
from core.cache import Cache
from core.logger import logger, request_logger

router = APIRouter(prefix="/library", tags=["library"])
permission = PermissionChecker(get_db(), Cache())


@router.get("/resources", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.READ)
async def get_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[int] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(async_db),
):
    """获取资源列表"""
    try:
        service = LibraryService(db, Cache())
        resources = await service.get_resources(
            skip=skip, limit=limit, category_id=category_id, type=type, search=search
        )
        return ResponseModel(data={"resources": [r.__dict__ for r in resources]})
    except Exception as e:
        logger.error(f"Failed to get resources: {str(e)}")
        raise HTTPException(status_code=500, detail="获取资源列表失败")


@router.get("/resources/{resource_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.READ)
async def get_resource(resource_id: int, db: Session = Depends(async_db)):
    """获取资源详情"""
    try:
        service = LibraryService(db, Cache())
        resource = await service.get_resource_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        return ResponseModel(data={"resource": resource.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get resource: {str(e)}")
        raise HTTPException(status_code=500, detail="获取资源信息失败")


@router.post("/resources", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.CREATE)
async def create_resource(resource: ResourceCreate, file: UploadFile = File(...), db: Session = Depends(async_db)):
    """创建资源"""
    try:
        service = LibraryService(db, Cache())
        new_resource = await service.create_resource(resource, file)
        return ResponseModel(message="创建资源成功", data={"resource": new_resource.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create resource: {str(e)}")
        raise HTTPException(status_code=500, detail="创建资源失败")


@router.put("/resources/{resource_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.UPDATE)
async def update_resource(resource_id: int, resource: ResourceUpdate, db: Session = Depends(async_db)):
    """更新资源信息"""
    try:
        service = LibraryService(db, Cache())
        updated_resource = await service.update_resource(resource_id, resource)
        return ResponseModel(message="更新资源成功", data={"resource": updated_resource.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update resource: {str(e)}")
        raise HTTPException(status_code=500, detail="更新资源失败")


@router.delete("/resources/{resource_id}", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.DELETE)
async def delete_resource(resource_id: int, db: Session = Depends(async_db)):
    """删除资源"""
    try:
        service = LibraryService(db, Cache())
        await service.delete_resource(resource_id)
        return ResponseModel(message="删除资源成功")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to delete resource: {str(e)}")
        raise HTTPException(status_code=500, detail="删除资源失败")


@router.get("/categories", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.READ)
async def get_categories(parent_id: Optional[int] = None, db: Session = Depends(async_db)):
    """获取资源分类"""
    try:
        service = LibraryService(db, Cache())
        categories = await service.get_categories(parent_id)
        return ResponseModel(data={"categories": [c.__dict__ for c in categories]})
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        raise HTTPException(status_code=500, detail="获取资源分类失败")


@router.post("/categories", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.CREATE)
async def create_category(
    name: str, parent_id: Optional[int] = None, description: Optional[str] = None, db: Session = Depends(async_db)
):
    """创建资源分类"""
    try:
        service = LibraryService(db, Cache())
        category = await service.create_category(name, parent_id, description)
        return ResponseModel(message="创建分类成功", data={"category": category.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to create category: {str(e)}")
        raise HTTPException(status_code=500, detail="创建资源分类失败")


@router.post("/resources/{resource_id}/borrow", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.UPDATE)
async def borrow_resource(resource_id: int, user_id: int, days: int = 30, db: Session = Depends(async_db)):
    """借阅资源"""
    try:
        service = LibraryService(db, Cache())
        record = await service.borrow_resource(resource_id, user_id, days)
        return ResponseModel(message="借阅成功", data={"record": record.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to borrow resource: {str(e)}")
        raise HTTPException(status_code=500, detail="借阅资源失败")


@router.post("/resources/{resource_id}/return", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.UPDATE)
async def return_resource(resource_id: int, user_id: int, db: Session = Depends(async_db)):
    """归还资源"""
    try:
        service = LibraryService(db, Cache())
        record = await service.return_resource(resource_id, user_id)
        return ResponseModel(message="归还成功", data={"record": record.__dict__})
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to return resource: {str(e)}")
        raise HTTPException(status_code=500, detail="归还资源失败")


@router.get("/borrowing-records", response_model=ResponseModel)
@permission.has_permission(ResourceType.LIBRARY, Action.READ)
async def get_borrowing_records(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(async_db),
):
    """获取借阅记录"""
    try:
        service = LibraryService(db, Cache())
        records = await service.get_borrowing_records(user_id=user_id, status=status, skip=skip, limit=limit)
        return ResponseModel(data={"records": [r.__dict__ for r in records]})
    except Exception as e:
        logger.error(f"Failed to get borrowing records: {str(e)}")
        raise HTTPException(status_code=500, detail="获取借阅记录失败")
