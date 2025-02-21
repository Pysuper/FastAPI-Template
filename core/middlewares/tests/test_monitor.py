import time
import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI

from ..monitor import RequestTracker, PerformanceAnalyzer, MonitorMiddleware


class TestRequestTracker(unittest.TestCase):
    """请求追踪器测试"""

    def setUp(self):
        self.tracker = RequestTracker()

    def test_duration_calculation(self):
        """测试持续时间计算"""
        # 模拟请求处理时间
        time.sleep(0.1)
        duration = self.tracker.duration

        self.assertGreater(duration, 0.1)
        self.assertLess(duration, 0.2)

    def test_finish_tracking(self):
        """测试完成追踪"""
        # 创建模拟响应
        response = Mock()
        response.status_code = 200
        response.body = b"test response"

        # 完成追踪
        self.tracker.finish(response)

        self.assertEqual(self.tracker.status_code, 200)
        self.assertEqual(self.tracker.response_size, 12)
        self.assertIsNotNone(self.tracker.end_time)


class TestPerformanceAnalyzer(unittest.TestCase):
    """性能分析器测试"""

    def setUp(self):
        self.analyzer = PerformanceAnalyzer()
        self.request = Mock()
        self.request.method = "GET"
        self.request.url.path = "/test"

    def test_analyze_slow_request(self):
        """测试分析慢请求"""
        tracker = RequestTracker()
        tracker.end_time = tracker.start_time + 2.0  # 模拟2秒的请求

        with self.assertLogs(self.analyzer.logger, level="WARNING") as logs:
            self.analyzer.analyze_request(self.request, tracker)

        self.assertTrue(any("Slow request detected" in msg for msg in logs.output))

    def test_analyze_large_request(self):
        """测试分析大请求"""
        tracker = RequestTracker()
        tracker.request_size = 2000000  # 2MB请求

        with self.assertLogs(self.analyzer.logger, level="WARNING") as logs:
            self.analyzer.analyze_request(self.request, tracker)

        self.assertTrue(any("Large request detected" in msg for msg in logs.output))

    def test_analyze_large_response(self):
        """测试分析大响应"""
        tracker = RequestTracker()
        tracker.response_size = 2000000  # 2MB响应

        with self.assertLogs(self.analyzer.logger, level="WARNING") as logs:
            self.analyzer.analyze_request(self.request, tracker)

        self.assertTrue(any("Large response detected" in msg for msg in logs.output))

    def test_analyze_error(self):
        """测试分析错误"""
        tracker = RequestTracker()
        tracker.error = ValueError("test error")

        with self.assertLogs(self.analyzer.logger, level="ERROR") as logs:
            self.analyzer.analyze_request(self.request, tracker)

        self.assertTrue(any("Request error" in msg for msg in logs.output))


class TestMonitorMiddleware(unittest.TestCase):
    """监控中间件测试"""

    def setUp(self):
        self.app = FastAPI()
        self.middleware = MonitorMiddleware(self.app, config={"slow_request_threshold": 1.0})
        self.request = Mock()
        self.request.method = "GET"
        self.request.url.path = "/test"
        self.request.state = Mock()

    async def test_process_request(self):
        """测试请求处理"""
        # 模拟请求体
        self.request.body = Mock()
        self.request.body.return_value = b"test request"

        await self.middleware.process_request(self.request)

        # 验证追踪器创建
        self.assertTrue(hasattr(self.request.state, "tracker"))

        # 验证指标更新
        labels = {"method": "GET", "path": "/test"}
        self.assertGreater(self.middleware.metrics.active_requests.labels(**labels)._value.get(), 0)

    async def test_process_response(self):
        """测试响应处理"""
        # 准备请求和响应
        await self.middleware.process_request(self.request)
        response = Mock()
        response.status_code = 200
        response.body = b"test response"

        # 处理响应
        result = await self.middleware.process_response(self.request, response)

        # 验证响应未被修改
        self.assertEqual(result, response)

        # 验证指标更新
        labels = {"method": "GET", "path": "/test"}
        self.assertEqual(self.middleware.metrics.active_requests.labels(**labels)._value.get(), 0)

    async def test_handle_exception(self):
        """测试异常处理"""
        # 准备请求
        await self.middleware.process_request(self.request)

        # 处理异常
        exc = ValueError("test error")
        with patch.object(self.middleware, "handle_exception", return_value=None) as mock_handle:
            await self.middleware.handle_exception(self.request, exc)

        # 验证错误指标更新
        labels = {"method": "GET", "path": "/test", "error_type": "ValueError"}
        self.assertGreater(self.middleware.metrics.error_count.labels(**labels)._value.get(), 0)

    def test_custom_threshold(self):
        """测试自定义阈值"""
        middleware = MonitorMiddleware(self.app, config={"slow_request_threshold": 2.0})
        self.assertEqual(middleware.analyzer.slow_request_threshold, 2.0)


if __name__ == "__main__":
    unittest.main()
