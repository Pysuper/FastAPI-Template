"""
测试模块
包含所有单元测试和集成测试
"""

import pytest
from typing import Generator, Dict

from fastapi.testclient import TestClient

from core import settings
from db.session import SessionLocal
from main import app


@pytest.fixture(scope="session")
def db() -> Generator:
    """
    数据库会话fixture
    """
    yield SessionLocal()


@pytest.fixture(scope="module")
def client() -> Generator:
    """
    测试客户端fixture
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    """
    超级用户认证头fixture
    """
    return {"Authorization": f"Bearer {settings.FIRST_SUPERUSER_TOKEN}"}
