from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.v1.endpoints.files.tools import BusinessError, validate_regex
from api.v1.endpoints.rbac.decorators import require_permissions, require_roles
from api.v1.endpoints.user.logs import log_error, operation_log
from core.dependencies.auth import get_current_user
from core.dependencies import async_db
from core.exceptions.base.error_codes import ErrorCode
from interceptor.response import ResponseSchema, success
from core.cache.decorators import clear_cache, cache_decorator
from core.utils.cache_warmer import warm_up_cache
from core.utils.export import DataExporter, DataImporter
from core.utils.query import QueryOptimizer
from models.department import Department
from schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate

router = APIRouter()


@router.post("/", response_model=ResponseSchema[DepartmentResponse])
@operation_log(module="部门管理", action="创建部门")
@require_permissions("department:create")
@require_roles("admin")
async def create_department(
    department: DepartmentCreate,
    request: Request,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """创建部门"""
    # 验证部门编码
    if not validate_regex(department.code, "department_code"):
        raise BusinessError(ErrorCode.INVALID_DEPARTMENT_CODE, "部门编码格式不正确")

    # 检查部门依赖关系
    if not check_department_dependencies(department.parent_id, db):
        raise BusinessError(ErrorCode.DEPARTMENT_DEPENDENCY_ERROR, "父级部门不可用")

    try:
        # 检查部门名称是否已存在
        if db.query(Department).filter(Department.name == department.name, Department.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Department name already exists")

        # 检查部门编码是否已存在
        if db.query(Department).filter(Department.code == department.code, Department.is_delete == False).first():
            raise HTTPException(status_code=400, detail="Department code already exists")

        # 检查父级部门是否存在
        parent_level = 0
        if department.parent_id:
            parent = db.query(Department).filter(Department.id == department.parent_id).first()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent department not found")
            parent_level = parent.level

        # 创建部门
        db_department = Department(
            name=department.name,
            code=department.code,
            description=department.description,
            parent_id=department.parent_id,
            sort=department.sort,
            level=parent_level + 1,
            leader=department.leader,
            phone=department.phone,
            email=department.email,
            address=department.address,
            is_system=department.is_system,
            remark=department.remark,
            create_by=current_user,
        )
        db.add(db_department)
        db.commit()
        db.refresh(db_department)

        # 清除相关缓存
        clear_cache("department:*")
        clear_cache("user:department:*")

        return success(data=db_department)

    except Exception as e:
        await log_error(db=db, module="部门管理", action="创建部门", error=e, user_id=current_user, request=request)
        raise


@router.get("/{department_id}", response_model=ResponseSchema[DepartmentResponse])
@cache_decorator(prefix="department", expire=3600)
async def get_department(
    department_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """获取部门详情"""
    department = db.query(Department).filter(Department.id == department_id, Department.is_delete == False).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return success(data=department)


@router.put("/{department_id}", response_model=ResponseSchema[DepartmentResponse])
async def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """更新部门信息"""
    department = db.query(Department).filter(Department.id == department_id, Department.is_delete == False).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # 不能修改系统部门
    if department.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system department")

    # 检查部门名称是否已存在
    if (
        department_update.name
        and db.query(Department)
        .filter(
            Department.name == department_update.name, Department.id != department_id, Department.is_delete == False
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Department name already exists")

    # 检查部门编码是否已存在
    if (
        department_update.code
        and db.query(Department)
        .filter(
            Department.code == department_update.code, Department.id != department_id, Department.is_delete == False
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="Department code already exists")

    # 检查父级部门是否存在
    if department_update.parent_id:
        parent = db.query(Department).filter(Department.id == department_update.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent department not found")
        # 更新层级
        department_update_dict = department_update.dict(exclude_unset=True)
        department_update_dict["level"] = parent.level + 1
    else:
        department_update_dict = department_update.dict(exclude_unset=True)

    # 检查状态是否有效
    if department_update.status:
        valid_statuses = ["active", "disabled"]
        if department_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    for field, value in department_update_dict.items():
        setattr(department, field, value)

    department.update_by = current_user
    department.update_time = datetime.now()

    db.add(department)
    db.commit()
    db.refresh(department)

    # 清除相关缓存
    clear_cache(f"department:{department_id}")
    clear_cache("department:list:*")
    clear_cache("department:tree:*")
    clear_cache("user:department:*")

    return success(data=department)


@router.delete("/{department_id}", response_model=ResponseSchema)
async def delete_department(
    department_id: int, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """删除部门"""
    department = db.query(Department).filter(Department.id == department_id, Department.is_delete == False).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # 不能删除系统部门
    if department.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system department")

    # 检查是否有用户使用该部门
    if db.query(User).filter(User.department_id == department_id, User.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Department is in use by users")

    # 检查是否有子部门
    if db.query(Department).filter(Department.parent_id == department_id, Department.is_delete == False).first():
        raise HTTPException(status_code=400, detail="Department has child departments")

    department.is_delete = True
    department.delete_by = current_user
    department.delete_time = datetime.now()

    db.add(department)
    db.commit()

    # 清除相关缓存
    clear_cache(f"department:{department_id}")
    clear_cache("department:list:*")
    clear_cache("department:tree:*")
    clear_cache("user:department:*")

    return success(message="Department deleted successfully")


@router.get("/", response_model=ResponseSchema[List[DepartmentResponse]])
@operation_log(module="部门管理", action="获取部门列表")
@require_permissions("department:list")
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(async_db),
    current_user: int = Depends(get_current_user),
):
    """获取部门列表"""
    # 构建查询条件
    filters = {}
    if keyword:
        filters["or"] = [
            {"name": {"ilike": f"%{keyword}%"}},
            {"code": {"ilike": f"%{keyword}%"}},
            {"description": {"ilike": f"%{keyword}%"}},
            {"leader": {"ilike": f"%{keyword}%"}},
        ]
    if status:
        filters["status"] = status

    # 构建排序条件
    order_by = ["level asc", "sort asc", "create_time desc"]

    # 执行查询
    result = QueryOptimizer.build_query(
        db=db,
        model=Department,
        filters=filters,
        order_by=order_by,
        page=skip // limit + 1,
        page_size=limit,
        cache_key=f"department:list:{skip}:{limit}:{keyword}:{status}",
        cache_expire=300,
    )

    return success(data=result[0], meta={"total": result[1], "skip": skip, "limit": limit})


@router.get("/tree", response_model=ResponseSchema)
@cache_decorator(prefix="department:tree", expire=3600)
async def get_department_tree(
    status: Optional[str] = None, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """获取部门树"""
    query = db.query(Department).filter(Department.is_delete == False)

    if status:
        query = query.filter(Department.status == status)

    departments = query.order_by(Department.level.asc(), Department.sort.asc()).all()

    def build_tree(parent_id: Optional[int] = None) -> List[dict]:
        nodes = []
        for department in departments:
            if department.parent_id == parent_id:
                node = {
                    "id": department.id,
                    "name": department.name,
                    "code": department.code,
                    "sort": department.sort,
                    "status": department.status,
                    "leader": department.leader,
                    "children": build_tree(department.id),
                }
                nodes.append(node)
        return nodes

    tree = build_tree()
    return success(data=tree)


@router.get("/stats", response_model=ResponseSchema)
@cache_decorator(prefix="department:stats", expire=300)
async def get_department_stats(db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """获取部门统计信息"""
    query = db.query(Department).filter(Department.is_delete == False)

    total_departments = query.count()
    active_departments = query.filter(Department.status == "active").count()
    disabled_departments = query.filter(Department.status == "disabled").count()
    system_departments = query.filter(Department.is_system == True).count()

    # 层级分布
    level_distribution = {
        level: count
        for level, count in db.query(Department.level, func.count(Department.id))
        .filter(Department.is_delete == False)
        .group_by(Department.level)
        .all()
    }

    # 用户分布
    user_distribution = {}
    departments = query.all()
    for department in departments:
        user_count = db.query(User).filter(User.department_id == department.id, User.is_delete == False).count()
        user_distribution[department.name] = user_count

    stats = {
        "total_departments": total_departments,
        "active_departments": active_departments,
        "disabled_departments": disabled_departments,
        "system_departments": system_departments,
        "level_distribution": level_distribution,
        "user_distribution": user_distribution,
    }

    return success(data=stats)


@router.post("/import", response_model=ResponseSchema)
@require_permissions("department:import")
async def import_departments(
    file: UploadFile = File(...), db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导入部门数据"""
    # 检查文件类型
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 保存文件
    filename = f"temp/department_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
    with open(filename, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # 导入数据
        if file_ext == "csv":
            imported_count = DataImporter.import_from_csv(filename, Department, db)
        elif file_ext == "xlsx":
            imported_count = DataImporter.import_from_excel(filename, Department, db)
        else:
            imported_count = DataImporter.import_from_json(filename, Department, db)

        # 清除缓存
        clear_cache("department:*")
        clear_cache("user:department:*")

        return success(message=f"Successfully imported {imported_count} departments")

    finally:
        # 删除临时文件
        import os

        os.remove(filename)


@router.get("/export", response_model=ResponseSchema)
@require_permissions("department:export")
async def export_departments(
    file_type: str, db: Session = Depends(async_db), current_user: int = Depends(get_current_user)
):
    """导出部门数据"""
    # 检查文件类型
    if file_type not in ["csv", "xlsx", "json"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 查询数据
    departments = db.query(Department).filter(Department.is_delete == False).all()
    data = [
        {
            "name": department.name,
            "code": department.code,
            "description": department.description,
            "parent_id": department.parent_id,
            "sort": department.sort,
            "status": department.status,
            "leader": department.leader,
            "phone": department.phone,
            "email": department.email,
            "address": department.address,
            "is_system": department.is_system,
            "remark": department.remark,
        }
        for department in departments
    ]

    # 导出文件
    filename = f"temp/department_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_type}"
    fields = [
        "name",
        "code",
        "description",
        "parent_id",
        "sort",
        "status",
        "leader",
        "phone",
        "email",
        "address",
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

        return success(data={"filename": f"departments.{file_type}", "content": content})

    finally:
        # 删除临时文件
        import os

        os.remove(filename)


@router.post("/cache/warm-up", response_model=ResponseSchema)
@require_permissions("department:cache")
async def warm_up_department_cache(db: Session = Depends(async_db), current_user: int = Depends(get_current_user)):
    """预热部门缓存"""
    # 预热部门树缓存
    await warm_up_cache(
        db=db,
        cache_key="department:tree",
        query_func=get_department_tree,
        params={"db": db, "current_user": current_user},
    )

    # 预热部门列表缓存
    await warm_up_cache(
        db=db,
        cache_key="department:list",
        query_func=list_departments,
        params={"db": db, "current_user": current_user, "skip": 0, "limit": 100},
    )

    # 预热部门统计缓存
    await warm_up_cache(
        db=db,
        cache_key="department:stats",
        query_func=get_department_stats,
        params={"db": db, "current_user": current_user},
    )

    return success(message="Department cache warmed up successfully")
