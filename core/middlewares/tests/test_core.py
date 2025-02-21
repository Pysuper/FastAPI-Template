import unittest

from fastapi import FastAPI

from ..core import MiddlewareStatus, MiddlewareRegistry, EnhancedMiddlewareManager


class TestMiddleware:
    """测试用中间件"""

    def __init__(self, app, **kwargs):
        self.app = app
        self.config = kwargs


class TestMiddlewareRegistry(unittest.TestCase):
    """中间件注册表测试"""

    def setUp(self):
        self.registry = MiddlewareRegistry()

    def test_register_middleware(self):
        """测试注册中间件"""
        # 注册中间件
        self.registry.register(
            name="test",
            middleware_class=TestMiddleware,
            description="Test middleware",
            version="1.0.0",
            dependencies={"auth"},
            order=1,
            config={"key": "value"},
        )

        # 验证注册结果
        metadata = self.registry.get_metadata("test")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.name, "test")
        self.assertEqual(metadata.description, "Test middleware")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.dependencies, {"auth"})
        self.assertEqual(metadata.order, 1)
        self.assertEqual(metadata.config, {"key": "value"})
        self.assertEqual(metadata.status, MiddlewareStatus.ENABLED)

    def test_register_duplicate_middleware(self):
        """测试重复注册中间件"""
        # 首次注册
        self.registry.register(name="test", middleware_class=TestMiddleware)

        # 重复注册应该抛出异常
        with self.assertRaises(ValueError):
            self.registry.register(name="test", middleware_class=TestMiddleware)

    def test_get_nonexistent_middleware(self):
        """测试获取不存在的中间件"""
        metadata = self.registry.get_metadata("nonexistent")
        self.assertIsNone(metadata)


class TestEnhancedMiddlewareManager(unittest.TestCase):
    """增强的中间件管理器测试"""

    def setUp(self):
        self.app = FastAPI()
        self.manager = EnhancedMiddlewareManager(self.app)

    def test_register_middleware(self):
        """测试注册中间件"""
        self.manager.register_middleware(name="test", middleware_class=TestMiddleware, dependencies={"auth"})

        # 验证注册结果
        metadata = self.manager.registry.get_metadata("test")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.name, "test")

    def test_enable_middleware(self):
        """测试启用中间件"""
        # 注册中间件
        self.manager.register_middleware(name="test", middleware_class=TestMiddleware)

        # 启用中间件
        self.manager.enable_middleware("test")

        # 验证状态
        metadata = self.manager.registry.get_metadata("test")
        self.assertEqual(metadata.status, MiddlewareStatus.ENABLED)

    def test_enable_nonexistent_middleware(self):
        """测试启用不存在的中间件"""
        with self.assertRaises(ValueError):
            self.manager.enable_middleware("nonexistent")

    def test_enable_middleware_with_missing_dependencies(self):
        """测试启用缺少依赖的中间件"""
        # 注册依赖于auth的中间件
        self.manager.register_middleware(name="test", middleware_class=TestMiddleware, dependencies={"auth"})

        # 启用应该失败
        with self.assertRaises(ValueError):
            self.manager.enable_middleware("test")

    def test_disable_middleware(self):
        """测试禁用中间件"""
        # 注册并启用中间件
        self.manager.register_middleware(name="test", middleware_class=TestMiddleware)
        self.manager.enable_middleware("test")

        # 禁用中间件
        self.manager.disable_middleware("test")

        # 验证状态
        metadata = self.manager.registry.get_metadata("test")
        self.assertEqual(metadata.status, MiddlewareStatus.DISABLED)

    def test_disable_middleware_with_dependents(self):
        """测试禁用有依赖者的中间件"""
        # 注册auth中间件
        self.manager.register_middleware(name="auth", middleware_class=TestMiddleware)

        # 注册依赖于auth的中间件
        self.manager.register_middleware(name="test", middleware_class=TestMiddleware, dependencies={"auth"})

        # 启用两个中间件
        self.manager.enable_middleware("auth")
        self.manager.enable_middleware("test")

        # 禁用auth应该失败
        with self.assertRaises(ValueError):
            self.manager.disable_middleware("auth")

    def test_reload_config(self):
        """测试重新加载配置"""
        # 注册中间件
        self.manager.register_middleware(name="test", middleware_class=TestMiddleware, config={"key": "value"})

        # 更新配置
        new_config = {"key": "new_value"}
        self.manager.reload_config("test", new_config)

        # 验证配置
        metadata = self.manager.registry.get_metadata("test")
        self.assertEqual(metadata.config["key"], "new_value")

    def test_get_middleware_status(self):
        """测试获取中间件状态"""
        # 注册中间件
        self.manager.register_middleware(
            name="test",
            middleware_class=TestMiddleware,
            description="Test middleware",
            version="1.0.0",
            dependencies={"auth"},
            order=1,
            config={"key": "value"},
        )

        # 获取状态
        status = self.manager.get_middleware_status()

        # 验证状态
        self.assertIn("test", status)
        test_status = status["test"]
        self.assertEqual(test_status["status"], "enabled")
        self.assertEqual(test_status["version"], "1.0.0")
        self.assertEqual(test_status["description"], "Test middleware")
        self.assertEqual(test_status["dependencies"], ["auth"])
        self.assertEqual(test_status["order"], 1)
        self.assertEqual(test_status["config"], {"key": "value"})


if __name__ == "__main__":
    unittest.main()
