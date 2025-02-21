from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.models import Role
from interceptor.response import ResponseSchema, success
from core.utils.logging import log_error, operation_log
from models.menu import Menu
from schemas.menus import MenuCreate, MenuResponse, MenuUpdate
from .decorators import require_permissions, require_roles

router = APIRouter(prefix="/menus", tags=["菜单管理"])


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
    try:
        # 检查菜单名称是否已存在
        if db.query(Menu).filter(Menu.name == menu.name, Menu.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Menu name already exists")

        # 检查父级菜单是否存在
        if menu.parent_id and not db.query(Menu).filter(Menu.id == menu.parent_id).first():
            raise HTTPException(status_code=404, detail="Parent menu not found")

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
            is_visible=menu.is_visible,
            is_cache=menu.is_cache,
            is_frame=menu.is_frame,
            permission=menu.permission,
            remark=menu.remark,
            create_by=current_user,
        )
        db.add(db_menu)
        db.commit()
        db.refresh(db_menu)
        return success(data=db_menu)

    except Exception as e:
        # 记录错误日志
        await log_error(db=db, module="菜单管理", action="创建菜单", error=e, user_id=current_user, request=request)
        raise


@router.get("/{menu_id}", response_model=ResponseSchema[MenuResponse])
async def get_menu(
    menu_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
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
    menu = (
        db.query(Menu)
        .filter(
            Menu.id == menu_id,
            Menu.is_delete == False,
        )
        .first()
    )
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # 检查菜单名称是否已存在
    if (
        menu_update.name
        and db.query(Menu)
        .filter(
            Menu.name == menu_update.name,
            Menu.id != menu_id,
            Menu.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Menu name already exists")

    # 检查父级菜单是否存在
    if menu_update.parent_id and not db.query(Menu).filter(Menu.id == menu_update.parent_id).first():
        raise HTTPException(status_code=404, detail="Parent menu not found")

    # 检查状态是否有效
    if menu_update.status:
        valid_statuses = ["active", "disabled"]
        if menu_update.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

    for field, value in menu_update.dict(exclude_unset=True).items():
        setattr(menu, field, value)

    menu.update_by = current_user
    menu.update_time = datetime.now()

    db.add(menu)
    db.commit()
    db.refresh(menu)
    return success(data=menu)


@router.delete("/{menu_id}", response_model=ResponseSchema)
async def delete_menu(
    menu_id: int,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """删除菜单"""
    menu = (
        db.query(Menu)
        .filter(
            Menu.id == menu_id,
            Menu.is_delete == False,
        )
        .first()
    )
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    # 检查是否有角色使用该菜单
    if (
        db.query(Role)
        .filter(
            Role.menu_ids.contains([menu_id]),
            Role.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Menu is in use by roles")

    # 检查是否有子菜单
    if (
        db.query(Menu)
        .filter(
            Menu.parent_id == menu_id,
            Menu.is_delete == False,
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Menu has child menus")

    menu.is_delete = True
    menu.delete_by = current_user
    menu.delete_time = datetime.now()

    db.add(menu)
    db.commit()
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
    query = db.query(Menu).filter(Menu.is_delete == False)

    if keyword:
        query = query.filter(
            or_(
                Menu.name.ilike(f"%{keyword}%"),
                Menu.path.ilike(f"%{keyword}%"),
                Menu.title.ilike(f"%{keyword}%"),
            )
        )
    if status:
        query = query.filter(Menu.status == status)
    if is_visible is not None:
        query = query.filter(Menu.is_visible == is_visible)

    total = query.count()
    menus = query.order_by(Menu.sort.asc()).offset(skip).limit(limit).all()

    return success(data=menus, meta={"total": total, "skip": skip, "limit": limit})


@router.put("/{menu_id}/status", response_model=ResponseSchema[MenuResponse])
async def update_menu_status(
    menu_id: int,
    status: str,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新菜单状态"""
    menu = (
        db.query(Menu)
        .filter(
            Menu.id == menu_id,
            Menu.is_delete == False,
        )
        .first()
    )
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    valid_statuses = ["active", "disabled"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    menu.status = status
    menu.update_by = current_user
    menu.update_time = datetime.now()

    db.add(menu)
    db.commit()
    db.refresh(menu)
    return success(data=menu)


@router.get("/tree", response_model=ResponseSchema)
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

    menus = query.order_by(Menu.sort.asc()).all()

    def build_tree(parent_id: Optional[int] = None) -> List[dict]:
        nodes = []
        for menu in menus:
            if menu.parent_id == parent_id:
                node = {
                    "id": menu.id,
                    "name": menu.name,
                    "path": menu.path,
                    "component": menu.component,
                    "redirect": menu.redirect,
                    "icon": menu.icon,
                    "title": menu.title,
                    "sort": menu.sort,
                    "status": menu.status,
                    "is_visible": menu.is_visible,
                    "is_cache": menu.is_cache,
                    "is_frame": menu.is_frame,
                    "permission": menu.permission,
                    "children": build_tree(menu.id),
                }
                nodes.append(node)
        return nodes

    tree = build_tree()
    return success(data=tree)


@router.get("/stats", response_model=ResponseSchema)
async def get_menu_stats(
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取菜单统计信息"""
    query = db.query(Menu).filter(Menu.is_delete == False)

    total_menus = query.count()
    active_menus = query.filter(Menu.status == "active").count()
    disabled_menus = query.filter(Menu.status == "disabled").count()
    visible_menus = query.filter(Menu.is_visible == True).count()
    hidden_menus = query.filter(Menu.is_visible == False).count()
    cached_menus = query.filter(Menu.is_cache == True).count()
    frame_menus = query.filter(Menu.is_frame == True).count()

    # 层级分布
    level_distribution = {}
    menus = query.all()

    def get_menu_level(menu_id: int, level: int = 1) -> int:
        menu = next((m for m in menus if m.id == menu_id), None)
        if not menu or not menu.parent_id:
            return level
        return get_menu_level(menu.parent_id, level + 1)

    for menu in menus:
        level = get_menu_level(menu.id)
        if level in level_distribution:
            level_distribution[level] += 1
        else:
            level_distribution[level] = 1

    # 角色分布
    role_distribution = {}
    for menu in menus:
        role_count = (
            db.query(Role)
            .filter(
                Role.menu_ids.contains([menu.id]),
                Role.is_delete == False,
            )
            .count()
        )
        role_distribution[menu.name] = role_count

    stats = {
        "total_menus": total_menus,
        "active_menus": active_menus,
        "disabled_menus": disabled_menus,
        "visible_menus": visible_menus,
        "hidden_menus": hidden_menus,
        "cached_menus": cached_menus,
        "frame_menus": frame_menus,
        "level_distribution": level_distribution,
        "role_distribution": role_distribution,
    }

    return success(data=stats)
