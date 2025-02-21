from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import validate_regex, BusinessError
from api.v1.endpoints.rbac.decorators import require_permissions, require_roles
from api.v1.endpoints.user.logs import log_error
from api.v1.endpoints.user.logs import operation_log
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.exceptions.base.error_codes import ErrorCode
from models.config import Config
from interceptor.response import ResponseSchema, success
from schemas.config import ConfigResponse, ConfigCreate, ConfigUpdate
from core.cache.decorators import cache_decorator, clear_cache
from core.utils.export import DataImporter, DataExporter
from core.utils.query import QueryOptimizer

# 路由
router = APIRouter()


@router.post("/", response_model=ResponseSchema[ConfigResponse])
@operation_log(module="系统配置", action="创建配置")
@require_permissions("config:create")
@require_roles("admin")
async def create_config(
    config: ConfigCreate,
    request: Request,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建配置"""
    # 验证配置键
    if not validate_regex(config.key, "config_key"):
        raise BusinessError(ErrorCode.INVALID_CONFIG_KEY, "配置键格式不正确")

    try:
        # 检查配置名称是否已存在
        if db.query(Config).filter(Config.name == config.name, Config.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Config name already exists")

        # 检查配置键是否已存在
        if db.query(Config).filter(Config.key == config.key, Config.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Config key already exists")

        # 检查配置类型是否有效
        valid_types = ["string", "number", "boolean", "json"]
        if config.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {', '.join(valid_types)}")

        # 验证配置值类型
        if config.type == "string" and not isinstance(config.value, str):
            raise HTTPException(status_code=400, detail="Value must be a string")
        elif config.type == "number" and not isinstance(config.value, (int, float)):
            raise HTTPException(status_code=400, detail="Value must be a number")
        elif config.type == "boolean" and not isinstance(config.value, bool):
            raise HTTPException(status_code=400, detail="Value must be a boolean")
        elif config.type == "json" and not isinstance(config.value, (dict, list)):
            raise HTTPException(status_code=400, detail="Value must be a JSON object or array")

        # 创建配置
        db_config = Config(
            name=config.name,
            key=config.key,
            value=config.value,
            type=config.type,
            group=config.group,
            description=config.description,
            is_system=config.is_system,
            remark=config.remark,
            create_by=current_user,
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)

        # 清除缓存
        clear_cache("config:*")

        return success(data=db_config)

    except Exception as e:
        # 记录错误日志
        await log_error(db=db, module="系统配置", action="创建配置", error=e, user_id=current_user, request=request)
        raise


@router.get("/{config_id}", response_model=ResponseSchema[ConfigResponse])
@cache_decorator(prefix="config", expire=3600)
async def get_config(config_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取配置详情"""
    config = db.query(Config).filter(Config.id == config_id, Config.is_delete == False).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return success(data=config)


@router.put("/{config_id}", response_model=ResponseSchema[ConfigResponse])
async def update_config(
    config_id: int,
    config_update: ConfigUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新配置信息"""
    config = db.query(Config).filter(Config.id == config_id, Config.is_delete == False).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # 不能修改系统配置
    if config.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system config")

    # 检查配置名称是否已存在
    if (
        config_update.name
        and db.query(Config)
        .filter(Config.name == config_update.name, Config.id != config_id, Config.is_delete == False)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Config name already exists")

    # 检查配置类型是否有效
    if config_update.type:
        valid_types = ["string", "number", "boolean", "json"]
        if config_update.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {', '.join(valid_types)}")

    # 检查状态是否有效
    if config_update.status:
        valid_statuses = ["active", "disabled"]
        if config_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    # 验证配置值类型
    if config_update.value is not None:
        config_type = config_update.type or config.type
        if config_type == "string" and not isinstance(config_update.value, str):
            raise HTTPException(status_code=400, detail="Value must be a string")
        elif config_type == "number" and not isinstance(config_update.value, (int, float)):
            raise HTTPException(status_code=400, detail="Value must be a number")
        elif config_type == "boolean" and not isinstance(config_update.value, bool):
            raise HTTPException(status_code=400, detail="Value must be a boolean")
        elif config_type == "json" and not isinstance(config_update.value, (dict, list)):
            raise HTTPException(status_code=400, detail="Value must be a JSON object or array")

    for field, value in config_update.dict(exclude_unset=True).items():
        setattr(config, field, value)

    config.update_by = current_user
    config.update_time = datetime.now()

    db.add(config)
    db.commit()
    db.refresh(config)

    # 清除缓存
    clear_cache("config:*")

    return success(data=config)


@router.delete("/{config_id}", response_model=ResponseSchema)
async def delete_config(config_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """删除配置"""
    config = db.query(Config).filter(Config.id == config_id, Config.is_delete == False).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # 不能删除系统配置
    if config.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system config")

    config.is_delete = True
    config.delete_by = current_user
    config.delete_time = datetime.now()

    db.add(config)
    db.commit()

    # 清除缓存
    clear_cache("config:*")

    return success(message="Config deleted successfully")


@router.get("/", response_model=ResponseSchema[List[ConfigResponse]])
@operation_log(module="系统配置", action="获取配置列表")
@require_permissions("config:list")
async def list_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    group: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取配置列表"""
    # 构建查询条件
    filters = {}
    if keyword:
        filters["name"] = {"ilike": keyword}
    if group:
        filters["group"] = group
    if type:
        filters["type"] = type
    if status:
        filters["status"] = status

    # 构建排序条件
    order_by = ["group asc", "key asc"]

    # 执行查询
    result = QueryOptimizer.build_query(
        db=db,
        model=Config,
        filters=filters,
        order_by=order_by,
        page=skip // limit + 1,
        page_size=limit,
        cache_key=f"config:list:{skip}:{limit}:{keyword}:{group}:{type}:{status}",
        cache_expire=300,
    )

    return success(data=result[0], meta={"total": result[1], "skip": skip, "limit": limit})


@router.put("/{config_id}/status", response_model=ResponseSchema[ConfigResponse])
async def update_config_status(
    config_id: int, status: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """更新配置状态"""
    config = db.query(Config).filter(Config.id == config_id, Config.is_delete == False).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # 不能修改系统配置状态
    if config.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system config status")

    valid_statuses = ["active", "disabled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    config.status = status
    config.update_by = current_user
    config.update_time = datetime.now()

    db.add(config)
    db.commit()
    db.refresh(config)

    # 清除缓存
    clear_cache("config:*")

    return success(data=config)


@router.get("/groups", response_model=ResponseSchema)
@cache_decorator(prefix="config", expire=3600)
async def get_config_groups(db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取配置分组列表"""
    groups = (
        db.query(Config.group)
        .filter(Config.is_delete == False)
        .group_by(Config.group)
        .order_by(Config.group.asc())
        .all()
    )
    return success(data=[group[0] for group in groups])


@router.get("/stats", response_model=ResponseSchema)
@cache_decorator(prefix="config", expire=300)
async def get_config_stats(db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取配置统计信息"""
    query = db.query(Config).filter(Config.is_delete == False)

    total_configs = query.count()
    active_configs = query.filter(Config.status == "active").count()
    disabled_configs = query.filter(Config.status == "disabled").count()
    system_configs = query.filter(Config.is_system == True).count()

    # 类型分布
    type_distribution = {
        type: count
        for type, count in db.query(Config.type, func.count(Config.id))
        .filter(Config.is_delete == False)
        .group_by(Config.type)
        .all()
    }

    # 分组分布
    group_distribution = {
        group: count
        for group, count in db.query(Config.group, func.count(Config.id))
        .filter(Config.is_delete == False)
        .group_by(Config.group)
        .all()
    }

    stats = {
        "total_configs": total_configs,
        "active_configs": active_configs,
        "disabled_configs": disabled_configs,
        "system_configs": system_configs,
        "type_distribution": type_distribution,
        "group_distribution": group_distribution,
    }

    return success(data=stats)


@router.post("/import", response_model=ResponseSchema)
@require_permissions("config:import")
async def import_configs(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导入配置"""
    # 检查文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 保存文件
    filename = f"temp/config_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
    with open(filename, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # 导入数据
        if file_ext == "csv":
            imported_count = DataImporter.import_from_csv(filename, Config, db)
        elif file_ext == "xlsx":
            imported_count = DataImporter.import_from_excel(filename, Config, db)
        else:
            imported_count = DataImporter.import_from_json(filename, Config, db)

        # 清除缓存
        clear_cache("config:*")

        return success(message=f"Successfully imported {imported_count} configs")

    finally:
        # 删除临时文件
        import os

        os.remove(filename)


@router.get("/export", response_model=ResponseSchema)
@require_permissions("config:export")
async def export_configs(
    file_type: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导出配置"""
    # 检查文件类型
    if file_type not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 查询数据
    configs = db.query(Config).filter(Config.is_delete == False).all()
    data = [
        {
            "name": config.name,
            "key": config.key,
            "value": config.value,
            "type": config.type,
            "group": config.group,
            "description": config.description,
            "status": config.status,
            "is_system": config.is_system,
            "remark": config.remark,
        }
        for config in configs
    ]

    # 导出文件
    filename = f"temp/config_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_type}"
    fields = ["name", "key", "value", "type", "group", "description", "status", "is_system", "remark"]

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

        return success(data={"filename": f"configs.{file_type}", "content": content})

    finally:
        # 删除临时文件
        import os

        os.remove(filename)
