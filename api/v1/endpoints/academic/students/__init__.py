from fastapi import APIRouter
from . import base, status, courses, grades

router = APIRouter(prefix="/students", tags=["学生管理"])

# 注册子路由
router.include_router(base.router)
router.include_router(status.router, prefix="/status")
router.include_router(courses.router, prefix="/courses")
router.include_router(grades.router, prefix="/grades") 