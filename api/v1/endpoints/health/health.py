from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import async_db
from utils.redis_cli import redis_client

router = APIRouter()


@router.get("/")
async def health_check(db: AsyncSession = Depends(async_db)):
    health_status = {
        "status": "healthy",
        "database": "unavailable",
        "redis": "unavailable",
    }

    try:
        # 检查数据库连接
        await db.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"

    try:
        # 检查Redis连接
        await redis_client.ping()
        health_status["redis"] = "healthy"
    except Exception:
        health_status["status"] = "unhealthy"

    return health_status
