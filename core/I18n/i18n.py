"""
国际化支持模块
实现多语言翻译和本地化
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config.manager import config_manager
from core.strong.event_bus import Event, event_bus

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """翻译错误"""

    pass


class Locale:
    """区域设置"""

    def __init__(self, code: str, name: str, fallback: Optional[str] = None):
        """
        初始化
        :param code: 语言代码
        :param name: 语言名称
        :param fallback: 回退语言
        """
        self.code = code
        self.name = name
        self.fallback = fallback
        self.translations: Dict[str, str] = {}

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class I18nManager:
    """国际化管理器"""

    def __init__(self):
        self._locales: Dict[str, Locale] = {}
        self._default_locale: Optional[str] = None
        self._lock = asyncio.Lock()
        self._initialized = False

    async def init(self) -> None:
        """初始化国际化管理器"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                # 加载区域设置
                await self._load_locales()

                # 设置默认区域
                self._default_locale = config_manager.i18n.DEFAULT_LOCALE
                if self._default_locale not in self._locales:
                    raise TranslationError(f"Default locale not found: {self._default_locale}")

                self._initialized = True
                logger.info("I18n manager initialized successfully")

            except Exception as e:
                logger.error("Failed to initialize i18n manager", exc_info=e)
                raise

    async def _load_locales(self) -> None:
        """加载区域设置"""
        locale_dir = Path(config_manager.i18n.LOCALE_DIR)
        if not locale_dir.exists():
            raise TranslationError(f"Locale directory not found: {locale_dir}")

        # 加载区域配置
        config_file = locale_dir / "locales.json"
        if not config_file.exists():
            raise TranslationError(f"Locale config not found: {config_file}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            for locale_code, locale_info in config.items():
                locale = Locale(
                    code=locale_code,
                    name=locale_info["name"],
                    fallback=locale_info.get("fallback"),
                )

                # 加载翻译文件
                translation_file = locale_dir / f"{locale_code}.json"
                if translation_file.exists():
                    with open(translation_file, "r", encoding="utf-8") as f:
                        locale.translations = json.load(f)

                self._locales[locale_code] = locale

        except Exception as e:
            raise TranslationError(f"Failed to load locales: {str(e)}")

    def get_locale(self, locale_code: Optional[str] = None) -> Locale:
        """
        获取区域设置
        :param locale_code: 语言代码
        :return: 区域设置
        """
        if not self._initialized:
            raise TranslationError("I18n manager not initialized")

        # 使用指定的区域设置
        if locale_code:
            locale = self._locales.get(locale_code)
            if locale:
                return locale

            # 尝试使用回退语言
            for code, l in self._locales.items():
                if l.fallback == locale_code:
                    return l

        # 使用默认区域设置
        return self._locales[self._default_locale]

    def translate(self, key: str, locale_code: Optional[str] = None, **params: Any) -> str:
        """
        翻译文本
        :param key: 翻译键
        :param locale_code: 语言代码
        :param params: 替换参数
        :return: 翻译后的文本
        """
        if not self._initialized:
            raise TranslationError("I18n manager not initialized")

        # 获取区域设置
        locale = self.get_locale(locale_code)

        # 查找翻译
        translation = locale.translations.get(key)
        if not translation and locale.fallback:
            # 使用回退语言
            fallback_locale = self._locales.get(locale.fallback)
            if fallback_locale:
                translation = fallback_locale.translations.get(key)

        if not translation:
            # 使用默认区域设置
            if locale.code != self._default_locale:
                translation = self._locales[self._default_locale].translations.get(key)

        if not translation:
            # 返回翻译键
            return key

        # 替换参数
        if params:
            try:
                return translation.format(**params)
            except KeyError as e:
                logger.warning(f"Missing translation parameter: {e}")
                return translation
            except Exception as e:
                logger.error(f"Error formatting translation: {e}")
                return translation

        return translation

    async def reload(self) -> None:
        """重新加载翻译"""
        if not self._initialized:
            raise TranslationError("I18n manager not initialized")

        async with self._lock:
            try:
                # 重新加载区域设置
                await self._load_locales()

                # 发布重新加载事件
                await event_bus.publish(
                    Event(
                        "i18n_reloaded",
                        {"locales": list(self._locales.keys())},
                    )
                )

                logger.info("I18n manager reloaded successfully")

            except Exception as e:
                logger.error("Failed to reload i18n manager", exc_info=e)
                raise

    def get_available_locales(self) -> List[str]:
        """
        获取可用的区域设置
        :return: 区域设置列表
        """
        return list(self._locales.keys())

    def get_default_locale(self) -> str:
        """
        获取默认区域设置
        :return: 默认区域设置
        """
        return self._default_locale

    async def add_translation(self, locale_code: str, key: str, value: str, persist: bool = True) -> None:
        """
        添加翻译
        :param locale_code: 语言代码
        :param key: 翻译键
        :param value: 翻译值
        :param persist: 是否持久化
        """
        if not self._initialized:
            raise TranslationError("I18n manager not initialized")

        locale = self._locales.get(locale_code)
        if not locale:
            raise TranslationError(f"Locale not found: {locale_code}")

        async with self._lock:
            # 更新翻译
            locale.translations[key] = value

            if persist:
                # 保存到文件
                translation_file = Path(config_manager.i18n.LOCALE_DIR) / f"{locale_code}.json"
                try:
                    with open(translation_file, "w", encoding="utf-8") as f:
                        json.dump(locale.translations, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.error(f"Failed to save translation: {e}")
                    raise TranslationError(f"Failed to save translation: {str(e)}")

            # 发布翻译更新事件
            await event_bus.publish(
                Event(
                    "translation_updated",
                    {
                        "locale": locale_code,
                        "key": key,
                        "value": value,
                    },
                )
            )

    async def remove_translation(self, locale_code: str, key: str, persist: bool = True) -> None:
        """
        删除翻译
        :param locale_code: 语言代码
        :param key: 翻译键
        :param persist: 是否持久化
        """
        if not self._initialized:
            raise TranslationError("I18n manager not initialized")

        locale = self._locales.get(locale_code)
        if not locale:
            raise TranslationError(f"Locale not found: {locale_code}")

        async with self._lock:
            # 删除翻译
            if key in locale.translations:
                del locale.translations[key]

                if persist:
                    # 保存到文件
                    translation_file = Path(config_manager.i18n.LOCALE_DIR) / f"{locale_code}.json"
                    try:
                        with open(translation_file, "w", encoding="utf-8") as f:
                            json.dump(locale.translations, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        logger.error(f"Failed to save translation: {e}")
                        raise TranslationError(f"Failed to save translation: {str(e)}")

                # 发布翻译删除事件
                await event_bus.publish(
                    Event(
                        "translation_removed",
                        {
                            "locale": locale_code,
                            "key": key,
                        },
                    )
                )


# 创建默认国际化管理器实例
i18n_manager = I18nManager()

# 导出
__all__ = [
    "i18n_manager",
    "I18nManager",
    "Locale",
    "TranslationError",
]
