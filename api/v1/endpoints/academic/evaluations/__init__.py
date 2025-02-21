from fastapi import APIRouter
from . import indicators, tasks, records

router = APIRouter(prefix="/evaluations", tags=["教学评价"])

# 注册子路由
router.include_router(indicators.router, prefix="/indicators")
router.include_router(tasks.router, prefix="/tasks")
router.include_router(records.router, prefix="/records") 