from fastapi import APIRouter
from . import base, titles, courses, attendance

router = APIRouter(prefix="/teachers", tags=["教师管理"])

# 注册子路由
router.include_router(base.router)
router.include_router(titles.router, prefix="/titles")
router.include_router(courses.router, prefix="/courses")
router.include_router(attendance.router, prefix="/attendance") 