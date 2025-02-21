# -*- coding:utf-8 -*-
"""
@Project ：Speedy 
@File    ：I18n.py
@Author  ：PySuper
@Date    ：2024/12/24 17:16 
@Desc    ：Speedy I18n.py
"""
import gettext
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from starlette.requests import Request
from starlette.responses import Response
from core.config.setting import settings
from middlewares.base import BaseCustomMiddleware


class I18nMiddleware(BaseCustomMiddleware):
    """
    国际化中间件
    处理多语言支持
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.default_locale = settings.i18n.default_locale
        self.supported_locales = settings.i18n.locales
        self.translations: Dict[str, gettext.GNUTranslations] = {}

        # 加载翻译文件
        for locale in self.supported_locales:
            try:
                # 加载翻译文件
                translation = gettext.translation("messages", settings.i18n.locale_path, languages=[locale])
                self.translations[locale] = translation
            except FileNotFoundError:
                # 如果找不到翻译文件，使用空翻译
                self.translations[locale] = gettext.NullTranslations()

        print(" ✅ I18nMiddleware")
        
    def _get_locale(self, request: Request) -> str:
        """获取请求的语言"""
        # 优先从查询参���获取
        locale = request.query_params.get("locale")
        if locale in self.supported_locales:
            return locale

        # 从Accept-Language头获取
        accept_language = request.headers.get("Accept-Language", "")
        if accept_language:
            # 解析Accept-Language
            locales = []
            for item in accept_language.split(","):
                if ";" in item:
                    lang, q = item.split(";")
                    q = float(q.split("=")[1])
                else:
                    lang = item
                    q = 1.0
                locales.append((lang.strip(), q))

            # 按q值排序
            locales.sort(key=lambda x: x[1], reverse=True)

            # 查找第一个支持的语言
            for lang, _ in locales:
                if lang in self.supported_locales:
                    return lang

        return self.default_locale

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 获取语言
        locale = self._get_locale(request)

        # 设置翻译器
        translator = self.translations[locale]
        request.state.locale = locale
        request.state.gettext = translator.gettext
        request.state.ngettext = translator.ngettext

        response = await call_next(request)

        # 添加语言响应头
        response.headers["Content-Language"] = locale

        return response
