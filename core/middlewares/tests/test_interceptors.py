import unittest
from unittest.mock import Mock

from fastapi import FastAPI
from starlette.datastructures import Headers

from ..exceptions import AuthorizationException
from ..interceptors import AuditInterceptor, SecurityInterceptor, CorsInterceptor, InterceptorMiddleware


class TestAuditInterceptor(unittest.TestCase):
    """审计拦截器测试"""

    def setUp(self):
        self.interceptor = AuditInterceptor()
        self.request = Mock()
        self.request.method = "GET"
        self.request.url.path = "/test"
        self.request.headers = Headers({"user-agent": "test-agent"})
        self.request.query_params = {}
        self.request.state = Mock()
        self.request.client = Mock()
        self.request.client.host = "127.0.0.1"

    async def test_before_request(self):
        """测试请求前处理"""
        await self.interceptor.before_request(self.request)

        # 验证审计日志创建
        self.assertTrue(hasattr(self.request.state, "audit_log"))
        self.assertTrue(hasattr(self.request.state, "start_time"))

        audit_log = self.request.state.audit_log
        self.assertEqual(audit_log.action, "GET")
        self.assertEqual(audit_log.resource, "/test")
        self.assertEqual(audit_log.ip_address, "127.0.0.1")
        self.assertEqual(audit_log.user_agent, "test-agent")

    async def test_after_request(self):
        """测试请求后处理"""
        # 准备请求
        await self.interceptor.before_request(self.request)

        # 准备响应
        response = Mock()
        response.status_code = 200
        response.headers = Headers()

        with self.assertLogs(self.interceptor.logger, level="INFO") as logs:
            await self.interceptor.after_request(self.request, response)

        # 验证日志记录
        self.assertTrue(any("Request audit" in msg for msg in logs.output))

    async def test_on_error(self):
        """测试错误处理"""
        # 准备请求
        await self.interceptor.before_request(self.request)

        # 准备异常
        exc = ValueError("test error")

        with self.assertLogs(self.interceptor.logger, level="ERROR") as logs:
            await self.interceptor.on_error(self.request, exc)

        # 验证错误日志
        self.assertTrue(any("Request error audit" in msg for msg in logs.output))


class TestSecurityInterceptor(unittest.TestCase):
    """安全拦截器测试"""

    def setUp(self):
        self.interceptor = SecurityInterceptor(allowed_hosts=["example.com"], allowed_methods=["GET", "POST"])
        self.request = Mock()
        self.request.method = "GET"
        self.request.headers = Headers({"host": "example.com"})

    def test_check_host(self):
        """测试主机名检查"""
        # 有效主机名
        self.assertTrue(self.interceptor._check_host(self.request))

        # 无效主机名
        self.request.headers = Headers({"host": "invalid.com"})
        self.assertFalse(self.interceptor._check_host(self.request))

    def test_check_method(self):
        """测试请求方法检查"""
        # 有效方法
        self.assertTrue(self.interceptor._check_method(self.request))

        # 无效方法
        self.request.method = "DELETE"
        self.assertFalse(self.interceptor._check_method(self.request))

    async def test_before_request(self):
        """测试请求前处理"""
        # 有效请求
        await self.interceptor.before_request(self.request)

        # 无效主机名
        self.request.headers = Headers({"host": "invalid.com"})
        with self.assertRaises(AuthorizationException):
            await self.interceptor.before_request(self.request)

        # 无效方法
        self.request.method = "DELETE"
        with self.assertRaises(AuthorizationException):
            await self.interceptor.before_request(self.request)

    async def test_after_request(self):
        """测试请求后处理"""
        response = Mock()
        response.headers = Headers()

        await self.interceptor.after_request(self.request, response)

        # 验证安全响应头
        self.assertIn("X-Content-Type-Options", response.headers)
        self.assertIn("X-Frame-Options", response.headers)
        self.assertIn("X-XSS-Protection", response.headers)


class TestCorsInterceptor(unittest.TestCase):
    """CORS拦截器测试"""

    def setUp(self):
        self.interceptor = CorsInterceptor(
            allow_origins=["http://example.com"],
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
            allow_credentials=True,
            max_age=3600,
        )
        self.request = Mock()
        self.request.headers = Headers({"origin": "http://example.com"})

    def test_get_origin(self):
        """测试获取请求源"""
        # 有效源
        origin = self.interceptor._get_origin(self.request)
        self.assertEqual(origin, "http://example.com")

        # 无效源
        self.request.headers = Headers({"origin": "http://invalid.com"})
        origin = self.interceptor._get_origin(self.request)
        self.assertIsNone(origin)

    async def test_before_response(self):
        """测试响应前处理"""
        response = Mock()
        response.headers = Headers()

        await self.interceptor.before_response(response)

        # 验证CORS响应头
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://example.com")
        self.assertEqual(response.headers["Access-Control-Allow-Methods"], "GET,POST")
        self.assertEqual(response.headers["Access-Control-Allow-Headers"], "Content-Type")
        self.assertEqual(response.headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(response.headers["Access-Control-Max-Age"], "3600")


class TestInterceptorMiddleware(unittest.TestCase):
    """拦截器中间件测试"""

    def setUp(self):
        self.app = FastAPI()
        self.middleware = InterceptorMiddleware(self.app)

        # 添加测试拦截器
        self.audit_interceptor = AuditInterceptor()
        self.security_interceptor = SecurityInterceptor()
        self.cors_interceptor = CorsInterceptor()

        self.middleware.add_request_interceptor(self.audit_interceptor)
        self.middleware.add_request_interceptor(self.security_interceptor)
        self.middleware.add_response_interceptor(self.cors_interceptor)

        self.request = Mock()
        self.request.method = "GET"
        self.request.url.path = "/test"
        self.request.headers = Headers()
        self.request.query_params = {}
        self.request.state = Mock()
        self.request.client = Mock()
        self.request.client.host = "127.0.0.1"

    async def test_process_request(self):
        """测试请求处理"""
        await self.middleware.process_request(self.request)

        # 验证请求拦截器执行
        self.assertTrue(hasattr(self.request.state, "audit_log"))

    async def test_process_response(self):
        """测试响应处理"""
        response = Mock()
        response.headers = Headers()

        processed_response = await self.middleware.process_response(self.request, response)

        # 验证响应拦截器执行
        self.assertIn("Access-Control-Allow-Origin", processed_response.headers)

    async def test_error_handling(self):
        """测试错误处理"""
        # 模拟拦截器错误
        self.request.headers = Headers({"host": "invalid.com"})

        with self.assertRaises(AuthorizationException):
            await self.middleware.process_request(self.request)


if __name__ == "__main__":
    unittest.main()
