# Файлы страниц документации для работы без интернета

Если в классе закрыт доступ к cdn.jsdelivr.net, положите в эту папку три файла
(скачайте их один раз на компьютере с интернетом):

| Файл | Адрес |
| --- | --- |
| `swagger-ui-bundle.js` | https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js |
| `swagger-ui.css` | https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css |
| `redoc.standalone.js` | https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js |

После перезапуска `fastapi dev main.py` страницы `/docs` и `/redoc` будут брать скрипты
из этой папки (модуль `offline_docs.py`). Если файлов нет, документация загружает их из сети.
