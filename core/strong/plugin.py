"""
插件系统
实现插件的动态加载和生命周期管理
"""

import importlib
import inspect
import logging
import os
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import jsonschema

from core.strong.event_bus import Event, event_bus

logger = logging.getLogger(__name__)


class PluginState(Enum):
    """插件状态"""

    UNLOADED = "unloaded"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """插件元数据"""

    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None
    entry_point: str = "plugin"
    config_schema: dict = None

    def __post_init__(self):
        self.dependencies = self.dependencies or []


class PluginError(Exception):
    """插件错误"""

    pass


class Plugin(ABC):
    """插件基类"""

    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.state = PluginState.UNLOADED
        self.config: Dict[str, Any] = {}
        self._event_handlers = {}

    @abstractmethod
    async def load(self) -> None:
        """加载插件"""
        try:
            # 设置状态为已加载
            self.state = PluginState.LOADED
            # 发布插件加载事件
            await event_bus.publish(Event("plugin_loaded", {"plugin": self.metadata.name}))
        except Exception as e:
            self.state = PluginState.ERROR
            logger.error(f"加载插件 {self.metadata.name} 失败: {e}")
            raise PluginError(f"加载插件失败: {str(e)}")

    @abstractmethod
    async def unload(self) -> None:
        """卸载插件"""
        try:
            # 取消注册所有事件处理器
            for event_type, handler in self._event_handlers.items():
                await event_bus.unsubscribe(event_type, handler)
            self._event_handlers.clear()

            # 设置状态为未加载
            self.state = PluginState.UNLOADED
            # 发布插件卸载事件
            await event_bus.publish(Event("plugin_unloaded", {"plugin": self.metadata.name}))
        except Exception as e:
            self.state = PluginState.ERROR
            logger.error(f"卸载插件 {self.metadata.name} 失败: {e}")
            raise PluginError(f"卸载插件失败: {str(e)}")

    @abstractmethod
    async def enable(self) -> None:
        """启用插件"""
        try:
            # 设置状态为已启用
            self.state = PluginState.ENABLED
            # 发布插件启用事件
            await event_bus.publish(Event("plugin_enabled", {"plugin": self.metadata.name}))
        except Exception as e:
            self.state = PluginState.ERROR
            logger.error(f"启用插件 {self.metadata.name} 失败: {e}")
            raise PluginError(f"启用插件失败: {str(e)}")

    @abstractmethod
    async def disable(self) -> None:
        """禁用插件"""
        try:
            # 设置状态为已禁用
            self.state = PluginState.DISABLED
            # 发布插件禁用事件
            await event_bus.publish(Event("plugin_disabled", {"plugin": self.metadata.name}))
        except Exception as e:
            self.state = PluginState.ERROR
            logger.error(f"禁用插件 {self.metadata.name} 失败: {e}")
            raise PluginError(f"禁用插件失败: {str(e)}")

    def configure(self, config: dict) -> None:
        """配置插件"""
        try:
            if self.metadata.config_schema:
                # 使用jsonschema验证配置
                try:
                    jsonschema.validate(instance=config, schema=self.metadata.config_schema)
                except jsonschema.exceptions.ValidationError as e:
                    raise PluginError(f"配置验证失败: {str(e)}")

                # 检查必填字段
                required = self.metadata.config_schema.get("required", [])
                for field in required:
                    if field not in config:
                        raise PluginError(f"缺少必填配置项: {field}")

                # 检查字段类型
                properties = self.metadata.config_schema.get("properties", {})
                for key, value in config.items():
                    if key in properties:
                        expected_type = properties[key].get("type")
                        if expected_type == "string" and not isinstance(value, str):
                            raise PluginError(f"配置项 {key} 必须是字符串类型")
                        elif expected_type == "number" and not isinstance(value, (int, float)):
                            raise PluginError(f"配置项 {key} 必须是数字类型")
                        elif expected_type == "boolean" and not isinstance(value, bool):
                            raise PluginError(f"配置项 {key} 必须是布尔类型")
                        elif expected_type == "array" and not isinstance(value, list):
                            raise PluginError(f"配置项 {key} 必须是数组类型")
                        elif expected_type == "object" and not isinstance(value, dict):
                            raise PluginError(f"配置项 {key} 必须是对象类型")

            self.config.update(config)
            logger.info(f"插件 {self.metadata.name} 配置已更新")
        except Exception as e:
            logger.error(f"配置插件 {self.metadata.name} 失败: {e}")
            raise PluginError(f"配置插件失败: {str(e)}")

    async def register_event_handler(self, event_type: str, handler: callable) -> None:
        """注册事件处理器"""
        await event_bus.subscribe(event_type, handler)
        self._event_handlers[event_type] = handler


class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self._plugins: Dict[str, Plugin] = {}
        self._load_order: List[str] = []

    async def discover(self) -> List[PluginMetadata]:
        """发现可用插件"""
        metadata_list = []

        # 确保插件目录存在
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            return metadata_list

        # 遍历插件目录
        for finder, name, _ in pkgutil.iter_modules([self.plugin_dir]):
            try:
                spec = finder.find_spec(name)
                if spec is None:
                    continue

                # 导入插件模块
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 获取插件元数据
                if hasattr(module, "PLUGIN_METADATA"):
                    metadata = module.PLUGIN_METADATA
                    if isinstance(metadata, dict):
                        metadata = PluginMetadata(**metadata)
                    metadata_list.append(metadata)

            except Exception as e:
                logger.error(f"Error discovering plugin {name}: {e}")

        return metadata_list

    async def load_plugin(self, metadata: PluginMetadata) -> None:
        """
        加载插件
        :param metadata: 插件元数据
        """
        if metadata.name in self._plugins:
            raise PluginError(f"Plugin {metadata.name} already loaded")

        # 检查依赖
        for dep in metadata.dependencies:
            if dep not in self._plugins:
                raise PluginError(f"Plugin {metadata.name} depends on {dep} which is not loaded")

        try:
            # 导入插件模块
            module = importlib.import_module(f"{self.plugin_dir}.{metadata.name}")

            # 获取插件类
            plugin_cls = None
            for item in dir(module):
                obj = getattr(module, item)
                if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                    plugin_cls = obj
                    break

            if not plugin_cls:
                raise PluginError(f"No plugin class found in {metadata.name}")

            # 创建插件实例
            plugin = plugin_cls(metadata)

            # 加载插件
            await plugin.load()
            plugin.state = PluginState.LOADED

            self._plugins[metadata.name] = plugin
            self._load_order.append(metadata.name)

            # 发布插件加载事件
            await event_bus.publish(Event("plugin_loaded", plugin))

        except Exception as e:
            logger.error(f"Error loading plugin {metadata.name}: {e}")
            raise PluginError(f"Failed to load plugin {metadata.name}: {str(e)}")

    async def unload_plugin(self, name: str) -> None:
        """
        卸载插件
        :param name: 插件名称
        """
        if name not in self._plugins:
            raise PluginError(f"Plugin {name} not loaded")

        # 检查依赖关系
        for plugin in self._plugins.values():
            if name in plugin.metadata.dependencies:
                raise PluginError(f"Cannot unload plugin {name}: plugin {plugin.metadata.name} depends on it")

        plugin = self._plugins[name]
        try:
            await plugin.unload()
            plugin.state = PluginState.UNLOADED

            del self._plugins[name]
            self._load_order.remove(name)

            # 发布插件卸载事件
            await event_bus.publish(Event("plugin_unloaded", plugin))

        except Exception as e:
            logger.error(f"Error unloading plugin {name}: {e}")
            plugin.state = PluginState.ERROR
            raise PluginError(f"Failed to unload plugin {name}: {str(e)}")

    async def enable_plugin(self, name: str) -> None:
        """
        启用插件
        :param name: 插件名称
        """
        if name not in self._plugins:
            raise PluginError(f"Plugin {name} not loaded")

        plugin = self._plugins[name]
        if plugin.state == PluginState.ENABLED:
            return

        try:
            await plugin.enable()
            plugin.state = PluginState.ENABLED

            # 发布插件启用事件
            await event_bus.publish(Event("plugin_enabled", plugin))

        except Exception as e:
            logger.error(f"Error enabling plugin {name}: {e}")
            plugin.state = PluginState.ERROR
            raise PluginError(f"Failed to enable plugin {name}: {str(e)}")

    async def disable_plugin(self, name: str) -> None:
        """
        禁用插件
        :param name: 插件名称
        """
        if name not in self._plugins:
            raise PluginError(f"Plugin {name} not loaded")

        plugin = self._plugins[name]
        if plugin.state == PluginState.DISABLED:
            return

        try:
            await plugin.disable()
            plugin.state = PluginState.DISABLED

            # 发布插件禁用事件
            await event_bus.publish(Event("plugin_disabled", plugin))

        except Exception as e:
            logger.error(f"Error disabling plugin {name}: {e}")
            plugin.state = PluginState.ERROR
            raise PluginError(f"Failed to disable plugin {name}: {str(e)}")

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取插件实例"""
        return self._plugins.get(name)

    def get_plugins(self) -> List[Plugin]:
        """获取所有插件"""
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> List[Plugin]:
        """获取所有已启用的插件"""
        return [p for p in self._plugins.values() if p.state == PluginState.ENABLED]

    async def load_all(self) -> None:
        """加载所有插件"""
        metadata_list = await self.discover()

        # 按依赖关系排序
        sorted_metadata = self._sort_by_dependencies(metadata_list)

        # 加载插件
        for metadata in sorted_metadata:
            try:
                await self.load_plugin(metadata)
            except Exception as e:
                logger.error(f"Failed to load plugin {metadata.name}: {e}")

    async def unload_all(self) -> None:
        """卸载所有插件"""
        # 按依赖关系反向卸载
        for name in reversed(self._load_order):
            try:
                await self.unload_plugin(name)
            except Exception as e:
                logger.error(f"Failed to unload plugin {name}: {e}")

    def _sort_by_dependencies(self, metadata_list: List[PluginMetadata]) -> List[PluginMetadata]:
        """按依赖关系排序插件"""
        sorted_list = []
        visited = set()

        def visit(metadata: PluginMetadata):
            if metadata.name in visited:
                return
            visited.add(metadata.name)

            # 先处理依赖
            for dep in metadata.dependencies:
                dep_metadata = next((m for m in metadata_list if m.name == dep), None)
                if dep_metadata:
                    visit(dep_metadata)

            sorted_list.append(metadata)

        for metadata in metadata_list:
            visit(metadata)

        return sorted_list


# 创建默认插件管理器实例
plugin_manager = PluginManager()

# 导出
__all__ = ["plugin_manager", "PluginManager", "Plugin", "PluginMetadata", "PluginState", "PluginError"]
