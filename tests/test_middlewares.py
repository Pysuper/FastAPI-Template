import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.middlewares.security import SecurityMiddleware
from core.middlewares.monitor import PerformanceMonitorMiddleware

@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    
    # 添加中间件
    app.add_middleware(
        SecurityMiddleware,
        config={
            "rate_limit": 2,  # 设置较小的限制以便测试
            "rate_limit_window": 1,
            "enable_sql_injection_check": True,
            "enable_xss_protection": True
        }
    )
    
    app.add_middleware(PerformanceMonitorMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
        
    @app.get("/sql-injection")
    async def sql_injection_endpoint(query: str):
        return {"query": query}
        
    return app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)

def test_rate_limit(client):
    """测试请求频率限制"""
    # 前两个请求应该成功
    for _ in range(2):
        response = client.get("/test")
        assert response.status_code == 200
        
    # 第三个请求应该被限制
    response = client.get("/test")
    assert response.status_code == 429
    assert "Too many requests" in response.text

def test_sql_injection_protection(client):
    """测试SQL注入保护"""
    # 正常查询
    response = client.get("/sql-injection?query=normal_query")
    assert response.status_code == 200
    
    # SQL注入尝试
    response = client.get("/sql-injection?query=SELECT * FROM users")
    assert response.status_code == 403
    assert "SQL injection" in response.text

def test_performance_monitoring(client):
    """测试性能监控"""
    response = client.get("/test")
    assert response.status_code == 200
    
    # 检查响应头中是否包含性能指标
    assert "X-Process-Time" in response.headers
    
def test_security_headers(client):
    """测试安全响应头"""
    response = client.get("/test")
    assert response.status_code == 200
    
    # 检查安全响应头
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"

def test_request_id(client):
    """测试请求ID"""
    response = client.get("/test")
    assert response.status_code == 200
    
    # 检查响应头中是否包含请求ID
    assert "X-Request-ID" in response.headers
    
@pytest.mark.asyncio
async def test_exception_handling(client):
    """测试异常处理"""
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
        
    response = client.get("/error")
    assert response.status_code == 500
    assert "error" in response.json()
    
def test_multiple_requests(client):
    """测试多个并发请求"""
    import concurrent.futures
    
    def make_request():
        return client.get("/test")
        
    # 创建5个并发请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(lambda _: make_request(), range(5)))
        
    # 检查响应
    success_count = sum(1 for r in responses if r.status_code == 200)
    rate_limited_count = sum(1 for r in responses if r.status_code == 429)
    
    # 由于速率限制，应该有一些成功的请求和一些被限制的请求
    assert success_count > 0
    assert rate_limited_count > 0
    assert success_count + rate_limited_count == 5 