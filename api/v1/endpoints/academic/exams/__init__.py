from fastapi import APIRouter
from . import base, schedule, grade

router = APIRouter(prefix="/exams", tags=["考试管理"])

# 注册子路由
router.include_router(base.router, prefix="")
router.include_router(schedule.router, prefix="/schedules")
router.include_router(grade.router, prefix="/grades") 