"""Готовый модуль: страницы документации /docs и /redoc без доступа к интернету.

Писать и менять этот файл не нужно.

Страницы /docs (Swagger UI) и /redoc (ReDoc) – это страницы HTML, которые загружают
свои скрипты и стили из сети доставки контента cdn.jsdelivr.net. Если в школьной сети
этот адрес закрыт, страница /docs остается белой. Тогда преподаватель один раз
скачивает три файла и кладет их в папку static/docs:

    static/docs/swagger-ui-bundle.js   https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js
    static/docs/swagger-ui.css         https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css
    static/docs/redoc.standalone.js    https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js

Если файлы на месте, приложение отдает документацию со своими файлами из /static/docs,
если нет – обычным способом, с файлами из сети. Способ взят из документации FastAPI,
раздел «Custom Docs UI Static Assets (Self-Hosting)».
"""

import pathlib

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent / "static" / "docs"   # папка server/static/docs
FILES = ("swagger-ui-bundle.js", "swagger-ui.css", "redoc.standalone.js")

LOCAL = all((DOCS_DIR / name).is_file() for name in FILES)

# Параметры для FastAPI(...): если файлы лежат рядом, встроенные страницы документации
# отключаются, и их заменяют страницы из функции add_offline_docs.
DOCS_SETTINGS = {"docs_url": None, "redoc_url": None} if LOCAL else {}


def add_offline_docs(app: FastAPI) -> None:
    """Добавляет страницы /docs и /redoc со своими файлами, если они скачаны в static/docs."""
    if not LOCAL:
        return

    @app.get("/docs", include_in_schema=False)
    def swagger_ui():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " – Swagger UI",
            swagger_js_url="/static/docs/swagger-ui-bundle.js",
            swagger_css_url="/static/docs/swagger-ui.css",
            swagger_favicon_url="/static/logo.svg",
        )

    @app.get("/redoc", include_in_schema=False)
    def redoc():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " – ReDoc",
            redoc_js_url="/static/docs/redoc.standalone.js",
            redoc_favicon_url="/static/logo.svg",
            with_google_fonts=False,
        )
