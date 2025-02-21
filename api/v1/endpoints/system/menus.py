from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import BusinessError, validate_regex
from api.v1.endpoints.rbac.decorators import require_permissions, require_roles
from api.v1.endpoints.user.logs import log_error
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.exceptions.base.error_codes import ErrorCode
from models import Role
from interceptor.response import ResponseSchema, success
from core.cache.decorators import clear_cache, cache_decorator
from core.utils.export import DataExporter, DataImporter
from core.utils.logging import operation_log
from core.utils.query import QueryOptimizer
from models.menu import Menu
from schemas.menus import MenuCreate, MenuResponse, MenuUpdate
from utils.cache_warmer import check_menu_dependencies, warm_up_cache

# 路由
router = APIRouter()


@router.post("/", response_model=ResponseSchema[MenuResponse])
@operation_log(module="菜单管理", action="创建菜单")
@require_permissions("menu:create")
@require_roles("admin")
async def create_menu(
    menu: MenuCreate,
    request: Request,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建菜单"""
    # 验证菜单名称
    if not validate_regex(menu.name, "menu_name"):
        raise BusinessError(ErrorCode.INVALID_MENU_NAME, "菜单名称格式不正确")

    # 检查菜单依赖关系
    if not check_menu_dependencies(menu.parent_id, db):
        raise BusinessError(ErrorCode.MENU_DEPENDENCY_ERROR, "父级菜单不可用")

    try:
        # 检查菜单名称是否已存在
        if db.query(Menu).filter(Menu.name == menu.name, Menu.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Menu name already exists")

        # 检查父级菜单是否存在
        parent_level = 0
        if menu.parent_id:
            parent = db.query(Menu).filter(Menu.id == menu.parent_id).first()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent menu not found")
            parent_level = parent.level

        # 创建菜单
        db_menu = Menu(
            name=menu.name,
            path=menu.path,
            component=menu.component,
            redirect=menu.redirect,
            icon=menu.icon,
            title=menu.title,
            parent_id=menu.parent_id,
            sort=menu.sort,
            level=parent_level + 1,
            permission=menu.permission,
            is_visible=menu.is_visible,
            is_cache=menu.is_cache,
            is_frame=menu.is_frame,
            is_system=menu.is_system,
            remark=menu.remark,
            create_by=current_user,
        )
        db.add(db_menu)
        db.commit()
        db.refresh(db_menu)

        # 清除相关缓存
        clear_cache("menu:*")
        clear_cache("role:menu:*")

        return success(data=db_menu)

    except Exception as e:
        await log_error(db=db, module="菜单管理", action="创建菜单", error=e, user_id=current_user, request=request)
        raise


@router.get("/{menu_id}", response_model=ResponseSchema[MenuResponse])
@cache_decorator(prefix="menu", expire=3600)
async def get_menu(menu_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取菜单详情"""
    menu = db.query(Menu).filter(Menu.id == menu_id, Menu.is_delete == False).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return success(data=menu)


@router.put("/{menu_id}", response_model=ResponseSchema[MenuResponse])
async def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新菜单信息"""
    menu = db.query(Menu).filter(Menu.id == menu_id, Menu.is_delete == False).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # 不能修改系统菜单
    if menu.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system menu")

    # 检查菜单名称是否已存在
    if (
        menu_update.name
        and db.query(Menu).filter(Menu.name == menu_update.name, Menu.id != menu_id, Menu.is_delete == False).first()
    ):
        raise HTTPException(status_code=400, detail="Menu name already exists")

    # 检查父级菜单是否存在
    if menu_update.parent_id:
        parent = db.query(Menu).filter(Menu.id == menu_update.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent menu not found")
        # 更新层级
        menu_update_dict = menu_update.dict(exclude_unset=True)
        menu_update_dict["level"] = parent.level + 1
    else:
        menu_update_dict = menu_update.dict(exclude_unset=True)

    # 检查状态是否有效
    if menu_update.status:
        valid_statuses = ["active", "disabled"]
        if menu_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    for field, value in menu_update_dict.items():
        setattr(menu, field, value)

    menu.update_by = current_user
    menu.update_time = datetime.now()

    db.add(menu)
    db.commit()
    db.refresh(menu)

    # 清除相关缓存
    clear_cache(f"menu:{menu_id}")
    clear_cache("menu:list:*")
    clear_cache("menu:tree:*")
    clear_cache("role:menu:*")

    return success(data=menu)


@router.delete("/{menu_id}", response_model=ResponseSchema)
async def delete_menu(menu_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """删除菜单"""
    menu = db.query(Menu).filter(Menu.id == menu_id, Menu.is_delete == False).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # 不能删除系统菜单
    if menu.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system menu")

    # 检查是否有角色使��该菜单
    if db.query(Role).filter(Role.menu_ids.contains([menu_id]), Role.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Menu is in use by roles")

    # 检查是否有子菜单
    if db.query(Menu).filter(Menu.parent_id == menu_id, Menu.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Menu has child menus")

    menu.is_delete = True
    menu.delete_by = current_user
    menu.delete_time = datetime.now()

    db.add(menu)
    db.commit()

    # 清除相关缓存
    clear_cache(f"menu:{menu_id}")
    clear_cache("menu:list:*")
    clear_cache("menu:tree:*")
    clear_cache("role:menu:*")

    return success(message="Menu deleted successfully")


@router.get("/", response_model=ResponseSchema[List[MenuResponse]])
@operation_log(module="菜单管理", action="获取菜单列表")
@require_permissions("menu:list")
async def list_menus(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    is_visible: Optional[bool] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取菜单列表"""
    # 构建查询条件
    filters = {}
    if keyword:
        filters["or"] = [
            {"name": {"ilike": f"%{keyword}%"}},
            {"title": {"ilike": f"%{keyword}%"}},
            {"path": {"ilike": f"%{keyword}%"}},
        ]
    if status:
        filters["status"] = status
    if is_visible is not None:
        filters["is_visible"] = is_visible

    # 构建排序条件
    order_by = ["level asc", "sort asc", "create_time desc"]

    # 执行查询
    result = QueryOptimizer.build_query(
        db=db,
        model=Menu,
        filters=filters,
        order_by=order_by,
        page=skip // limit + 1,
        page_size=limit,
        cache_key=f"menu:list:{skip}:{limit}:{keyword}:{status}:{is_visible}",
        cache_expire=300,
    )

    return success(data=result[0], meta={"total": result[1], "skip": skip, "limit": limit})


@router.get("/tree", response_model=ResponseSchema)
@cache_decorator(prefix="menu:tree", expire=3600)
async def get_menu_tree(
    status: Optional[str] = None,
    is_visible: Optional[bool] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取菜单树"""
    query = db.query(Menu).filter(Menu.is_delete == False)

    if status:
        query = query.filter(Menu.status == status)
    if is_visible is not None:
        query = query.filter(Menu.is_visible == is_visible)

    menus = query.order_by(Menu.level.asc(), Menu.sort.asc()).all()

    def build_tree(parent_id: Optional[int] = None) -> List[dict]:
        nodes = []
        for menu in menus:
            if menu.parent_id == parent_id:
                node = {
                    "id": menu.id,
                    "name": menu.name,
                    "title": menu.title,
                    "path": menu.path,
                    "component": menu.component,
                    "icon": menu.icon,
                    "sort": menu.sort,
                    "status": menu.status,
                    "is_visible": menu.is_visible,
                    "children": build_tree(menu.id),
                }
                nodes.append(node)
        return nodes

    tree = build_tree()
    return success(data=tree)


@router.get("/stats", response_model=ResponseSchema)
@cache_decorator(prefix="menu:stats", expire=300)
async def get_menu_stats(db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取菜单统计信息"""
    query = db.query(Menu).filter(Menu.is_delete == False)

    total_menus = query.count()
    active_menus = query.filter(Menu.status == "active").count()
    disabled_menus = query.filter(Menu.status == "disabled").count()
    system_menus = query.filter(Menu.is_system == True).count()
    visible_menus = query.filter(Menu.is_visible == True).count()
    cached_menus = query.filter(Menu.is_cache == True).count()
    frame_menus = query.filter(Menu.is_frame == True).count()

    # 层级分布
    level_distribution = {
        level: count
        for level, count in db.query(Menu.level, func.count(Menu.id))
        .filter(Menu.is_delete == False)
        .group_by(Menu.level)
        .all()
    }

    # 角色分布
    role_distribution = {}
    menus = query.all()
    for menu in menus:
        role_count = db.query(Role).filter(Role.menu_ids.contains([menu.id]), Role.is_delete == False).count()
        role_distribution[menu.name] = role_count

    stats = {
        "total_menus": total_menus,
        "active_menus": active_menus,
        "disabled_menus": disabled_menus,
        "system_menus": system_menus,
        "visible_menus": visible_menus,
        "cached_menus": cached_menus,
        "frame_menus": frame_menus,
        "level_distribution": level_distribution,
        "role_distribution": role_distribution,
    }

    return success(data=stats)


@router.post("/import", response_model=ResponseSchema)
@require_permissions("menu:import")
async def import_menus(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导入菜单数据"""
    # 检查文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 保存文件
    filename = f"temp/menu_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
    with open(filename, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # 导入数据
        if file_ext == "csv":
            imported_count = DataImporter.import_from_csv(filename, Menu, db)
        elif file_ext == "xlsx":
            imported_count = DataImporter.import_from_excel(filename, Menu, db)
        else:
            imported_count = DataImporter.import_from_json(filename, Menu, db)

        # 清除缓存
        clear_cache("menu:*")
        clear_cache("role:menu:*")

        return success(message=f"Successfully imported {imported_count} menus")

    finally:
        # 删除临时文件
        import os

        os.remove(filename)


@router.get("/export", response_model=ResponseSchema)
@require_permissions("menu:export")
async def export_menus(file_type: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """导出菜单数据"""
    # 检查文件类型
    if file_type not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 查询数据
    menus = db.query(Menu).filter(Menu.is_delete == False).all()
    data = [
        {
            "name": menu.name,
            "path": menu.path,
            "component": menu.component,
            "redirect": menu.redirect,
            "icon": menu.icon,
            "title": menu.title,
            "parent_id": menu.parent_id,
            "sort": menu.sort,
            "permission": menu.permission,
            "status": menu.status,
            "is_visible": menu.is_visible,
            "is_cache": menu.is_cache,
            "is_frame": menu.is_frame,
            "is_system": menu.is_system,
            "remark": menu.remark,
        }
        for menu in menus
    ]

    # 导出文件
    filename = f"temp/menu_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_type}"
    fields = [
        "name",
        "path",
        "component",
        "redirect",
        "icon",
        "title",
        "parent_id",
        "sort",
        "permission",
        "status",
        "is_visible",
        "is_cache",
        "is_frame",
        "is_system",
        "remark",
    ]

    try:
        if file_type == "csv":
            DataExporter.export_to_csv(data, fields, filename)
        elif file_type == "xlsx":
            DataExporter.export_to_excel(data, fields, filename)
        else:
            DataExporter.export_to_json(data, filename)

        # 读取文件内容
        with open(filename, "rb") as f:
            content = f.read()

        return success(data={"filename": f"menus.{file_type}", "content": content})

    finally:
        # 删除临时文件
        import os

        os.remove(filename)


@router.post("/cache/warm-up", response_model=ResponseSchema)
@require_permissions("menu:cache")
async def warm_up_menu_cache(db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """预热菜单缓存"""
    # 预热菜单树缓存
    await warm_up_cache(
        db=db, cache_key="menu:tree", query_func=get_menu_tree, params={"db": db, "current_user": current_user}
    )

    # 预热菜单列表缓存
    await warm_up_cache(
        db=db,
        cache_key="menu:list",
        query_func=list_menus,
        params={"db": db, "current_user": current_user, "skip": 0, "limit": 100},
    )

    # 预热菜单统计缓存
    await warm_up_cache(
        db=db, cache_key="menu:stats", query_func=get_menu_stats, params={"db": db, "current_user": current_user}
    )

    return success(message="Menu cache warmed up successfully")
