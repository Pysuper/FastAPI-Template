# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：files.py
@Author  ：PySuper
@Date    ：2024/12/20 14:44 
@Desc    ：文件管理模块

提供文件上传、下载、管理等功能
支持文件夹管理、文件搜索和权限控制
"""
from pathlib import Path
from typing import List, Optional, Dict, Any

from core.dependencies.permissions import requires_permissions
from core.dependencies.rate_limit import rate_limiter
from fastapi import Body, Depends, File, Path as PathParam, Query, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from services.file.file_service import FileService
from sqlalchemy.orm import Session

from api.base.crud import CRUDRouter
from core.cache.config.config import CacheConfig
from core.dependencies import async_db
from models.file import (
    FileModel,
    FileCreate,
    FileUpdate,
    FileFilter,
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    FileResponse,
)
from schemas.base.response import Response

# 缓存配置
FILE_CACHE_CONFIG = {
    "strategy": "redis",
    "prefix": "file:",
    "serializer": "json",
    "settings": CacheConfig,
    "enable_stats": True,
    "enable_memory_cache": True,
    "enable_redis_cache": True,
    "ttl": 3600,  # 缓存1小时
}

router = CRUDRouter(
    model=FileModel,
    create_schema=FileCreate,
    update_schema=FileUpdate,
    filter_schema=FileFilter,
    prefix="/files",
    tags=["文件管理"],
    cache_config=FILE_CACHE_CONFIG,
)


@router.router.post(
    "/upload", response_model=Response[FileResponse], summary="上传文件", description="上传文件到指定文件夹"
)
@rate_limiter(max_requests=10, window_seconds=60)  # 每分钟最多10次上传请求
@requires_permissions(["upload_file"])
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Query(None, description="文件夹ID"),
    description: Optional[str] = Query(None, description="文件描述"),
    tags: Optional[List[str]] = Query(None, description="文件标签"),
    db: Session = Depends(async_db),
) -> Response[FileResponse]:
    """上传文件

    Args:
        file: 要上传的文件
        folder_id: 可选的目标文件夹ID
        description: 可选的文件描述
        tags: 可选的文件标签列表
        db: 数据库会话

    Returns:
        包含上传文件信息的响应对象

    Raises:
        HTTPException: 上传失败时抛出
    """
    try:
        # 验证文件大小
        file_size = await file.seek(0, 2)  # 获取文件大小
        if file_size > 100 * 1024 * 1024:  # 100MB限制
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="文件大小超过限制")

        # 上传文件
        file_info = await FileService.upload_file(db, file, folder_id=folder_id, description=description, tags=tags)

        return Response(code=201, message="文件上传成功", data=file_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件上传失败: {str(e)}")


@router.router.get("/download/{file_id}", response_class=FileResponse, summary="下载文件", description="下载指定的文件")
@requires_permissions(["download_file"])
async def download_file(
    file_id: int = PathParam(..., description="文件ID"), db: Session = Depends(async_db)
) -> FileResponse:
    """下载文件

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        文件响应对象

    Raises:
        HTTPException: 下载失败时抛出
    """
    try:
        # 获取文件信息
        file_info = await FileService.get_file_info(db, file_id)
        if not file_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

        # 检查文件是否存在
        file_path = Path(file_info.path)
        if not file_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

        # 更新下载次数
        await FileService.increment_download_count(db, file_id)

        return FileResponse(path=str(file_path), filename=file_info.name, media_type=file_info.mime_type)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件下载失败: {str(e)}")


@router.router.post(
    "/folders", response_model=Response[FolderResponse], summary="创建文件夹", description="创建新的文件夹"
)
@requires_permissions(["create_folder"])
async def create_folder(
    data: FolderCreate = Body(..., description="文件夹创建数据"), db: Session = Depends(async_db)
) -> Response[FolderResponse]:
    """创建文件夹

    Args:
        data: 文件夹创建数据
        db: 数据库会话

    Returns:
        包含新创建的文件夹信息的响应对象

    Raises:
        HTTPException: 创建失败时抛出
    """
    try:
        folder = await FileService.create_folder(db, data)
        return Response(code=201, message="文件夹创建成功", data=folder)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件夹创建失败: {str(e)}")


@router.router.put(
    "/folders/{folder_id}",
    response_model=Response[FolderResponse],
    summary="更新文件夹",
    description="更新指定文件夹的信息",
)
@requires_permissions(["update_folder"])
async def update_folder(
    folder_id: int = PathParam(..., description="文件夹ID"),
    data: FolderUpdate = Body(..., description="文件夹更新数据"),
    db: Session = Depends(async_db),
) -> Response[FolderResponse]:
    """更新文件夹

    Args:
        folder_id: 文件夹ID
        data: 文件夹更新数据
        db: 数据库会话

    Returns:
        包含更新后的文件夹信息的响应对象

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        folder = await FileService.update_folder(db, folder_id, data)
        return Response(code=200, message="文件夹更新成功", data=folder)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件夹更新失败: {str(e)}")


@router.router.delete(
    "/folders/{folder_id}", response_model=Response, summary="删除文件夹", description="删除指定的文件夹及其内容"
)
@requires_permissions(["delete_folder"])
async def delete_folder(
    folder_id: int = PathParam(..., description="文件夹ID"),
    recursive: bool = Query(False, description="是否递归删除子文件夹"),
    db: Session = Depends(async_db),
) -> Response:
    """删除文件夹

    Args:
        folder_id: 文件夹ID
        recursive: 是否递归删除子文件夹
        db: 数据库会话

    Returns:
        删除操作的响应对象

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        await FileService.delete_folder(db, folder_id, recursive=recursive)
        return Response(code=200, message="文件夹删除成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件夹删除失败: {str(e)}")


@router.router.get(
    "/folders",
    response_model=Response[List[FolderResponse]],
    summary="获取文件夹列表",
    description="获取文件夹列表，支持分页和层级结构",
)
@requires_permissions(["view_folders"])
async def get_folders(
    parent_id: Optional[int] = Query(None, description="父文件夹ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    recursive: bool = Query(False, description="是否递归获取子文件夹"),
    db: Session = Depends(async_db),
) -> Response[List[FolderResponse]]:
    """获取文件夹列表

    Args:
        parent_id: 可选的父文件夹ID
        page: 页码，从1开始
        page_size: 每页记录数
        recursive: 是否递归获取子文件夹
        db: 数据库会话

    Returns:
        包含文件夹列表的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        folders = await FileService.get_folders(
            db, parent_id=parent_id, skip=(page - 1) * page_size, limit=page_size, recursive=recursive
        )
        return Response(code=200, message="获取文件夹列表成功", data=folders)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取文件夹列表失败: {str(e)}")


@router.router.post(
    "/move", response_model=Response[FileResponse], summary="移动文件", description="将文件移动到指定文件夹"
)
@requires_permissions(["move_file"])
async def move_file(
    file_id: int = Query(..., description="文件ID"),
    target_folder_id: Optional[int] = Query(None, description="目标文件夹ID"),
    db: Session = Depends(async_db),
) -> Response[FileResponse]:
    """移动文件

    Args:
        file_id: 文件ID
        target_folder_id: 目标文件夹ID，None表示移动到根目录
        db: 数据库会话

    Returns:
        包含移动后的文件信息的响应对象

    Raises:
        HTTPException: 移动失败时抛出
    """
    try:
        file = await FileService.move_file(db, file_id, target_folder_id)
        return Response(code=200, message="文件移动成功", data=file)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件移动失败: {str(e)}")


@router.router.post(
    "/copy", response_model=Response[FileResponse], summary="复制文件", description="将文件复制到指定文件夹"
)
@requires_permissions(["copy_file"])
async def copy_file(
    file_id: int = Query(..., description="文件ID"),
    target_folder_id: Optional[int] = Query(None, description="目标文件夹ID"),
    db: Session = Depends(async_db),
) -> Response[FileResponse]:
    """复制文件

    Args:
        file_id: 文件ID
        target_folder_id: 目标文件夹ID，None表示复制到根目录
        db: 数据库会话

    Returns:
        包含复制后的文件信息的响应对象

    Raises:
        HTTPException: 复制失败时抛出
    """
    try:
        file = await FileService.copy_file(db, file_id, target_folder_id)
        return Response(code=200, message="文件复制成功", data=file)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件复制失败: {str(e)}")


@router.router.post(
    "/rename", response_model=Response[FileResponse], summary="重命名文件", description="重命名指定的文件"
)
@requires_permissions(["rename_file"])
async def rename_file(
    file_id: int = Query(..., description="文件ID"),
    new_name: str = Query(..., description="新文件名"),
    db: Session = Depends(async_db),
) -> Response[FileResponse]:
    """重命名文件

    Args:
        file_id: 文件ID
        new_name: 新文件名
        db: 数据库会话

    Returns:
        包含重命名后的文件信息的响应对象

    Raises:
        HTTPException: 重命名失败时抛出
    """
    try:
        file = await FileService.rename_file(db, file_id, new_name)
        return Response(code=200, message="文件重命名成功", data=file)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件重命名失败: {str(e)}")


@router.router.get(
    "/search", response_model=Response[List[FileResponse]], summary="搜索文件", description="根据条件搜索文件"
)
@requires_permissions(["search_files"])
async def search_files(
    keyword: str = Query(..., description="搜索关键词"),
    file_type: Optional[str] = Query(None, description="文件类型"),
    folder_id: Optional[int] = Query(None, description="文件夹ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    order_by: Optional[str] = Query("created_at", description="排序字段"),
    order_desc: bool = Query(True, description="是否降序排序"),
    db: Session = Depends(async_db),
) -> Response[List[FileResponse]]:
    """搜索文件

    Args:
        keyword: 搜索关键词
        file_type: 可选的文件类型过滤
        folder_id: 可选的文件夹ID过滤
        page: 页码，从1开始
        page_size: 每页记录数
        order_by: 排序字段
        order_desc: 是否降序排序
        db: 数据库会话

    Returns:
        包含搜索结果的响应对象

    Raises:
        HTTPException: 搜索失败时抛出
    """
    try:
        files = await FileService.search_files(
            db,
            keyword,
            file_type=file_type,
            folder_id=folder_id,
            skip=(page - 1) * page_size,
            limit=page_size,
            order_by=order_by,
            order_desc=order_desc,
        )
        return Response(code=200, message="搜索成功", data=files)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件搜索失败: {str(e)}")


# 新增API端点
@router.router.get(
    "/{file_id}/info",
    response_model=Response[Dict[str, Any]],
    summary="获取文件详细信息",
    description="获取指定文件的详细信息，包括元数据",
)
@requires_permissions(["view_file_info"])
async def get_file_info(
    file_id: int = PathParam(..., description="文件ID"), db: Session = Depends(async_db)
) -> Response[Dict[str, Any]]:
    """获取文件详细信息

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        包含文件详细信息的响应对象

    Raises:
        HTTPException: 查询失败时抛出
    """
    try:
        file_info = await FileService.get_file_details(db, file_id)
        return Response(code=200, message="获取文件信息成功", data=file_info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取文件信息失败: {str(e)}")


@router.router.post("/batch-delete", response_model=Response, summary="批量删除文件", description="批量删除指定的文件")
@requires_permissions(["delete_files"])
async def batch_delete_files(
    file_ids: List[int] = Body(..., description="文件ID列表"), db: Session = Depends(async_db)
) -> Response:
    """批量删除文件

    Args:
        file_ids: 要删除的文件ID列表
        db: 数据库会话

    Returns:
        删除操作的响应对象

    Raises:
        HTTPException: 删除失败时抛出
    """
    try:
        await FileService.batch_delete_files(db, file_ids)
        return Response(code=200, message="文件批量删除成功")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"文件批量删除失败: {str(e)}")
