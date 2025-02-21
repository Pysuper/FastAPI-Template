from typing import Optional

from fastapi import Query

from schemas.base.pagination import PaginationParams


async def get_pagination_params(
    page: Optional[int] = Query(1, ge=1, description="页码"),
    size: Optional[int] = Query(10, ge=1, le=100, description="每页数量"),
) -> PaginationParams:
    """
    获取分页参数
    """
    return PaginationParams(page=page, size=size)
