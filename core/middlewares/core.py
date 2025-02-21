import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Set, Type

from fastapi import FastAPI


class MiddlewareStatus(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class MiddlewareMetadata:
    name: str
    description: str
    version: str
    dependencies: Set[str]
    order: int
    status: MiddlewareStatus
    config: Dict[str, Any]


class MiddlewareRegistry:
    """中间件注册表"""

    def __init__(self):
        self._middlewares: Dict[str, MiddlewareMetadata] = {}
        self._instances: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def register(
        self,
        name: str,
        middleware_class: Type,
        description: str = "",
        version: str = "1.0.0",
        dependencies: Set[str] = None,
        order: int = 0,
        config: Dict[str, Any] = None,
    ) -> None:
        """注册中间件"""
        if name in self._middlewares:
            raise ValueError(f"Middleware {name} already registered")

        metadata = MiddlewareMetadata(
            name=name,
            description=description,
            version=version,
            dependencies=dependencies or set(),
            order=order,
            status=MiddlewareStatus.ENABLED,
            config=config or {},
        )
        self._middlewares[name] = metadata
        self.logger.info(f"Registered middleware: {name}")

    def get_metadata(self, name: str) -> Optional[MiddlewareMetadata]:
        """获取中间件元数据"""
        return self._middlewares.get(name)

    def get_instance(self, name: str) -> Optional[Any]:
        """获取中间件实例"""
        return self._instances.get(name)

    def set_instance(self, name: str, instance: Any) -> None:
        """设置中间件实例"""
        self._instances[name] = instance


class EnhancedMiddlewareManager:
    """增强的中间件管理器"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.registry = MiddlewareRegistry()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_dependencies: Dict[str, Set[str]] = {}

    def register_middleware(
        self,
        name: str,
        middleware_class: Type,
        description: str = "",
        version: str = "1.0.0",
        dependencies: Set[str] = None,
        order: int = 0,
        config: Dict[str, Any] = None,
    ) -> None:
        """注册中间件"""
        # 注册到注册表
        self.registry.register(
            name=name,
            middleware_class=middleware_class,
            description=description,
            version=version,
            dependencies=dependencies,
            order=order,
            config=config,
        )

        # 更新依赖图
        if dependencies:
            self._dependency_graph[name] = dependencies
            for dep in dependencies:
                if dep not in self._reverse_dependencies:
                    self._reverse_dependencies[dep] = set()
                self._reverse_dependencies[dep].add(name)

    def enable_middleware(self, name: str) -> None:
        """启用中间件"""
        metadata = self.registry.get_metadata(name)
        if not metadata:
            raise ValueError(f"Middleware {name} not found")

        # 检查依赖
        for dep in metadata.dependencies:
            dep_metadata = self.registry.get_metadata(dep)
            if not dep_metadata or dep_metadata.status != MiddlewareStatus.ENABLED:
                raise ValueError(f"Dependency {dep} not enabled")

        # ��建实例并添加到FastAPI
        instance = self._create_middleware_instance(name)
        self.registry.set_instance(name, instance)
        metadata.status = MiddlewareStatus.ENABLED
        self.app.add_middleware(instance.__class__, **metadata.config)
        self.logger.info(f"Enabled middleware: {name}")

    def disable_middleware(self, name: str) -> None:
        """禁用中间件"""
        metadata = self.registry.get_metadata(name)
        if not metadata:
            raise ValueError(f"Middleware {name} not found")

        # 检查反向依赖
        if name in self._reverse_dependencies:
            deps = self._reverse_dependencies[name]
            for dep in deps:
                dep_metadata = self.registry.get_metadata(dep)
                if dep_metadata and dep_metadata.status == MiddlewareStatus.ENABLED:
                    raise ValueError(f"Cannot disable {name}, {dep} depends on it")

        metadata.status = MiddlewareStatus.DISABLED
        self.registry.set_instance(name, None)
        self.logger.info(f"Disabled middleware: {name}")

    def _create_middleware_instance(self, name: str) -> Any:
        """创建中间件实例"""
        metadata = self.registry.get_metadata(name)
        if not metadata:
            raise ValueError(f"Middleware {name} not found")

        try:
            instance = metadata.__class__(self.app, **metadata.config)
            return instance
        except Exception as e:
            metadata.status = MiddlewareStatus.ERROR
            self.logger.error(f"Failed to create middleware instance {name}: {str(e)}")
            raise

    def get_middleware_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有中间件状态"""
        status = {}
        for name, metadata in self.registry._middlewares.items():
            status[name] = {
                "status": metadata.status.value,
                "version": metadata.version,
                "description": metadata.description,
                "dependencies": list(metadata.dependencies),
                "order": metadata.order,
                "config": metadata.config,
            }
        return status

    def reload_config(self, name: str, config: Dict[str, Any]) -> None:
        """重新加载中间件配置"""
        metadata = self.registry.get_metadata(name)
        if not metadata:
            raise ValueError(f"Middleware {name} not found")

        # 更新配置
        metadata.config.update(config)

        # 如果中间件已启用,重新创建实例
        if metadata.status == MiddlewareStatus.ENABLED:
            self.disable_middleware(name)
            self.enable_middleware(name)
            self.logger.info(f"Reloaded middleware config: {name}")
