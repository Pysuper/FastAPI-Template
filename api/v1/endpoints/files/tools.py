import re
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from core.dependencies import async_db
from models.department import Department
from models.permission import Permission
from models.role import Role
from models.user import User
from schemas.base.response import Response

router = APIRouter(prefix="/tools", tags=["工具"])

# 正则表达式验证规则
REGEX_PATTERNS = {
    # 用户名:3-20位字母数字下划线
    "username": r"^[a-zA-Z0-9_-]{3,20}$",
    # 密码:至少8位,包含字母和数字
    "password": r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$",
    # 手机号:11位数字
    "phone": r"^1[3-9]\d{9}$",
    # 邮箱
    "email": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
    # 角色编码:2-50位大写字母下划线
    "role_code": r"^[A-Z_]{2,50}$",
    # 权限编码:2-50位大写字母下划线
    "permission_code": r"^[A-Z_]{2,50}$",
    # 部门编码:2-50位大写字母数字
    "department_code": r"^[A-Z0-9]{2,50}$",
}

# 敏感词列表(示例)
SENSITIVE_WORDS = [
    "admin",
    "root",
    "system",
    "test",
]


def validate_regex(value: str, pattern_name: str) -> bool:
    """正则表达式验证"""
    if pattern_name not in REGEX_PATTERNS:
        raise ValueError(f"Unknown pattern: {pattern_name}")
    pattern = REGEX_PATTERNS[pattern_name]
    return bool(re.match(pattern, value))


def contains_sensitive_words(text: str) -> bool:
    """检查是否包含敏感词"""
    return any(word in text.lower() for word in SENSITIVE_WORDS)


def check_password_strength(password: str) -> bool:
    """检查密码强度"""
    # 长度至少8位
    if len(password) < 8:
        return False
    # 必须包含字母和数字
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    # 必须包含特殊字符
    if not re.search(r"[@$!%*#?&]", password):
        return False
    return True


def check_department_capacity(department_id: int, db) -> bool:
    """检查部门是否已满员"""
    # 获取部门配置的最大人数
    department = db.query(Department).get(department_id)
    if not department:
        return False
    max_users = department.max_users or 100  # 默认最大100人

    # 获取当前部门人数
    current_users = (
        db.query(User)
        .filter(
            User.department_id == department_id,
            User.is_delete == False,
        )
        .count()
    )

    return current_users < max_users


def check_role_depth(parent_id: Optional[int], db, max_depth: int = 5) -> bool:
    """检查角色层级深度"""
    if not parent_id:
        return True

    depth = 1
    current_role = db.query(Role).get(parent_id)
    while current_role and current_role.parent_id:
        depth += 1
        if depth > max_depth:
            return False
        current_role = db.query(Role).get(current_role.parent_id)
    return True


def check_permission_conflicts(permission_ids: List[int], db) -> bool:
    """检查权限是否冲突"""
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()

    # 检查是否存在互斥的权限
    for i, p1 in enumerate(permissions):
        for p2 in permissions[i + 1 :]:
            if p1.is_conflict_with(p2):
                return True
    return False


def check_permission_dependencies(parent_id: Optional[int], db) -> bool:
    """检查权限依赖关系"""
    if not parent_id:
        return True

    parent = db.query(Permission).get(parent_id)
    if not parent:
        return False

    # 检查父权限的状态
    if parent.status != "active":
        return False

    return True


# 业务错误码定义
class ErrorCode:
    # 用户相关:1xxxx
    USER_NOT_FOUND = 10001
    USER_ALREADY_EXISTS = 10002
    USER_DISABLED = 10003
    USER_LOCKED = 10004
    INVALID_PASSWORD = 10005

    # 角色相关:2xxxx
    ROLE_NOT_FOUND = 20001
    ROLE_ALREADY_EXISTS = 20002
    ROLE_IN_USE = 20003
    ROLE_DEPTH_EXCEEDED = 20004

    # 权限相关:3xxxx
    PERMISSION_NOT_FOUND = 30001
    PERMISSION_ALREADY_EXISTS = 30002
    PERMISSION_IN_USE = 30003
    PERMISSION_CONFLICT = 30004

    # 部门相关:4xxxx
    DEPARTMENT_NOT_FOUND = 40001
    DEPARTMENT_ALREADY_EXISTS = 40002
    DEPARTMENT_IN_USE = 40003
    DEPARTMENT_FULL = 40004


# 自定义业务异常
class BusinessError(HTTPException):
    def __init__(self, code: int, message: str):
        super().__init__(status_code=400, detail={"code": code, "message": message})


@router.post("/excel/import", response_model=Response, summary="导入Excel")
async def import_excel(
    file: UploadFile = File(...),
    sheet_name: str = Query(None, description="工作表名称"),
    start_row: int = Query(1, ge=1, description="起始行"),
    db: Session = Depends(async_db),
):
    """导入Excel"""

    return Response(data={})


@router.get("/excel/export", response_model=Response, summary="导出Excel")
async def export_excel(
    data: dict = Body(..., description="导出数据"),
    file_name: str = Query(..., description="文件名"),
    sheet_name: str = Query(None, description="工作表名称"),
    db: Session = Depends(async_db),
):
    """导出Excel"""

    return Response(data={})


@router.post("/word/import", response_model=Response, summary="导入Word")
async def import_word(file: UploadFile = File(...), db: Session = Depends(async_db)):
    """导入Word"""

    return Response(data={})


@router.get("/word/export", response_model=Response, summary="导出Word")
async def export_word(
    data: dict = Body(..., description="导出数据"),
    file_name: str = Query(..., description="文件名"),
    db: Session = Depends(async_db),
):
    """导出Word"""

    return Response(data={})


@router.post("/pdf/import", response_model=Response, summary="导入PDF")
async def import_pdf(file: UploadFile = File(...), db: Session = Depends(async_db)):
    """导入PDF"""

    return Response(data={})


@router.get("/pdf/export", response_model=Response, summary="导出PDF")
async def export_pdf(
    data: dict = Body(..., description="导出数据"),
    file_name: str = Query(..., description="文件名"),
    db: Session = Depends(async_db),
):
    """导出PDF"""

    return Response(data={})


@router.post("/image/compress", response_model=Response, summary="压缩图片")
async def compress_image(
    file: UploadFile = File(...),
    quality: int = Query(80, ge=1, le=100, description="压缩质量"),
    db: Session = Depends(async_db),
):
    """压缩图片"""

    return Response(data={})


@router.post("/image/convert", response_model=Response, summary="转换图片格式")
async def convert_image(
    file: UploadFile = File(...),
    format: str = Query(..., description="目标格式"),
    db: Session = Depends(async_db),
):
    """转换图片格式"""

    return Response(data={})


@router.post("/video/compress", response_model=Response, summary="压缩视频")
async def compress_video(
    file: UploadFile = File(...),
    quality: int = Query(80, ge=1, le=100, description="压缩质量"),
    db: Session = Depends(async_db),
):
    """压缩视频"""

    return Response(data={})


@router.post("/video/convert", response_model=Response, summary="转换视频格式")
async def convert_video(
    file: UploadFile = File(...),
    format: str = Query(..., description="目标格式"),
    db: Session = Depends(async_db),
):
    """转换视频格式"""

    return Response(data={})
