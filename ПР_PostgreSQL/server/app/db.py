"""Т4.Б1.4, задание З4. Соединение с базой данных PostgreSQL – одно на запрос.

Места, которые нужно дописать, отмечены комментарием # <--
"""

from typing import Annotated

import psycopg
from fastapi import Depends
from psycopg.rows import dict_row

from app.config import settings


def get_conn():
    """Зависимость FastAPI: открывает соединение с базой на время обработки запроса.

    Блок with у соединения psycopg в конце подтверждает изменения (COMMIT),
    при исключении внутри блока отменяет их (ROLLBACK), а затем закрывает соединение.
    """
    # <-- with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
    #         yield conn
    #     Вызывайте именно psycopg.connect(...): тест считает соединения через эту функцию.
    raise NotImplementedError("З4: напишите get_conn в app/db.py")
    yield   # заглушка: из-за yield Python считает функцию генератором, удалите эту строку


# Тип параметра для обработчиков: conn: Conn. Готово.
# scope="function": соединение закрывается (и изменения подтверждаются) после выполнения
# функции маршрута, но ДО отправки ответа клиенту. Иначе клиент мог бы получить ответ 201
# раньше, чем запись будет подтверждена в базе.
Conn = Annotated[psycopg.Connection, Depends(get_conn, scope="function")]
