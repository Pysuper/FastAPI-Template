from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from interceptor.response import ResponseSchema, success
from core.cache.decorators import clear_cache
from core.utils.cache_warmer import warm_up_cache

router = APIRouter(prefix="/cache", tags=["缓存管理"])


@router.post("/warm-up/{module}", response_model=ResponseSchema)
async def warm_up_module_cache(
    module: str,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
) -> Dict[str, str]:
    """预热指定模块的缓存"""
    # 根据模块名称获取相应的查询函数和缓存键
    module_configs = {
        "user": [
            {"key": "user:list", "func": "list_users", "params": {"skip": 0, "limit": 100}},
            {"key": "user:stats", "func": "get_user_stats", "params": {}},
        ],
        "role": [
            {"key": "role:list", "func": "list_roles", "params": {"skip": 0, "limit": 100}},
            {"key": "role:stats", "func": "get_role_stats", "params": {}},
        ],
        "menu": [
            {"key": "menu:list", "func": "list_menus", "params": {"skip": 0, "limit": 100}},
            {"key": "menu:tree", "func": "get_menu_tree", "params": {}},
            {"key": "menu:stats", "func": "get_menu_stats", "params": {}},
        ],
        "department": [
            {"key": "department:list", "func": "list_departments", "params": {"skip": 0, "limit": 100}},
            {"key": "department:tree", "func": "get_department_tree", "params": {}},
            {"key": "department:stats", "func": "get_department_stats", "params": {}},
        ],
    }

    if module not in module_configs:
        raise HTTPException(status_code=400, detail=f"Invalid module: {module}")

    results = {}
    for config in module_configs[module]:
        try:
            # 从相应的模块导入函数
            module_name = f"api.v1.endpoints.system.{module}s"
            module_obj = __import__(module_name, fromlist=[config["func"]])
            func = getattr(module_obj, config["func"])

            # 预热缓存
            params = {**config["params"], "db": db, "current_user": current_user}
            await warm_up_cache(
                db=db,
                cache_key=config["key"],
                query_func=func,
                params=params,
            )
            results[config["key"]] = "success"
        except Exception as e:
            results[config["key"]] = str(e)

    return success(data=results)


@router.post("/warm-up", response_model=ResponseSchema)
async def warm_up_all_cache(
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
) -> Dict[str, Dict[str, str]]:
    """预热所有缓存"""
    results = {}
    modules = ["user", "role", "menu", "department"]

    for module in modules:
        try:
            result = await warm_up_module_cache(module=module, db=db, current_user=current_user)
            results[module] = result.get("data", {})
        except Exception as e:
            results[module] = {"error": str(e)}

    return success(data=results)


@router.delete("/{pattern}", response_model=ResponseSchema)
async def clear_cache_by_pattern(
    pattern: str,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
) -> Dict[str, int]:
    """清除指定模式的缓存"""
    count = clear_cache(pattern)
    return success(data={"cleared": count})
