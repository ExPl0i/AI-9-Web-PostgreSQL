"""Т4.Б1.4. Хранение данных: PostgreSQL и драйвер psycopg 3.

Программный интерфейс из Т4.Б1.3 теперь хранит поездки не в словаре, а в базе данных PostgreSQL:
данные переживают перезапуск сервера.
Запуск (в папке server, сервер PostgreSQL запущен, таблицы созданы командой python -m app.init_db):
    fastapi dev app/main.py
затем в браузере http://127.0.0.1:8000/docs.

Задания:
    З1  сервер PostgreSQL, роль и базы (db/setup.sql), файл .env; проверка – маршрут /api/health
    З2  десять SQL-запросов к архиву поездок: файлы sql/q01.sql–sql/q10.sql
    З3  схема schema.sql и создание таблиц app/init_db.py
    З4  зависимость get_conn в app/db.py: одно соединение на запрос
    З5  маршруты /api/trips на SQL: SELECT, INSERT ... RETURNING, UPDATE, DELETE
    З6  сводка по покрытиям GET /api/trips/summary (GROUP BY)

Повышенная сложность (pytest -m extra): таблица автомобилей (sql/cars.sql) и GET /api/cars с JOIN.

Места, которые нужно дописать, отмечены комментарием # <--
Условия заданий – в файле ЗАДАНИЯ.md.
"""

import datetime
from enum import StrEnum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import BASE_DIR
from app.db import Conn
from app.errors import NOT_JSON, describe_all, http_error_text, is_json_error
from app.offline_docs import DOCS_SETTINGS, add_offline_docs

SURFACE_NAMES = {"dry": "сухой асфальт", "wet": "мокрый асфальт", "dirt": "грунт", "snow": "снег и лед"}
SURFACE_MU = {"dry": 0.7, "wet": 0.4, "dirt": 0.5, "snow": 0.15}
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

TAGS = [
    {"name": "Служебное", "description": "Проверка связи с базой данных"},
    {"name": "Покрытия", "description": "Справочник типов дорожного покрытия"},
    {"name": "Поездки", "description": "Журнал поездок в базе данных PostgreSQL"},
    {"name": "Автомобили", "description": "Автопарк (повышенная сложность)"},
]

app = FastAPI(
    title="Покрытие",
    version="0.4.0",
    description="Программный интерфейс учебного сервиса беспилотного автомобиля. Данные хранятся в PostgreSQL. "
                "Занятие Т4.Б1.4.",
    openapi_tags=TAGS,
    **DOCS_SETTINGS,
)
add_offline_docs(app)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


# ---------------------------------------------------------------- Модели (готовы из Т4.Б1.3)

class Surface(StrEnum):
    """Допустимые коды покрытия."""
    dry = "dry"
    wet = "wet"
    dirt = "dirt"
    snow = "snow"


class TripIn(BaseModel):
    """Поездка, которую присылает клиент."""
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"date": "2026-11-05", "distance": 12.5, "surface": "wet", "note": "дождь после обеда"}],
    })

    date: datetime.date = Field(description="Дата поездки в виде ГГГГ-ММ-ДД")
    distance: float = Field(gt=0, le=2000, description="Расстояние, км: больше 0 и не больше 2000")
    surface: Surface = Field(description="Покрытие: dry, wet, dirt или snow")
    note: str = Field(default="", max_length=200, description="Комментарий водителя, не длиннее 200 символов")


class TripOut(BaseModel):
    """Поездка в ответе сервера: без служебных полей."""
    id: int = Field(description="Номер поездки")
    date: datetime.date
    distance: float = Field(description="Расстояние, км")
    surface: Surface
    note: str
    created_at: datetime.datetime = Field(description="Когда сервер принял поездку")


class TripSort(StrEnum):
    """Порядок списка поездок. Минус перед именем поля – по убыванию."""
    id = "id"
    date = "date"
    date_desc = "-date"
    distance = "distance"
    distance_desc = "-distance"


class SurfaceSummary(BaseModel):
    """З6. Сводка по одному покрытию."""
    surface: Surface
    trips: int = Field(description="Число поездок")
    avg_distance: float = Field(description="Средний пробег, км, с округлением до 0,1")


class CarOut(BaseModel):
    """Повышенная сложность. Автомобиль и его пробег."""
    id: int
    plate: str = Field(description="Бортовой номер")
    model: str = Field(description="Модель")
    trips: int = Field(description="Число поездок")
    total_distance: float = Field(description="Общий пробег, км")


TripId = Annotated[int, Path(ge=1, description="Номер поездки, начиная с 1")]
NOT_FOUND = {404: {"description": "Поездки с таким номером нет"}}

# Столбцы, которые уходят клиенту. Служебный client_host из базы даже не читаем.
TRIP_COLUMNS = "id, date, distance, surface, note, created_at"

# Порядок сортировки -> готовый кусок SQL. Значение sort приходит от клиента, поэтому в текст
# запроса подставляется не оно само, а кусок из этого словаря: другого текста попасть туда не может.
ORDER_BY = {
    TripSort.id: "id",
    TripSort.date: "date, id",
    # <-- допишите TripSort.date_desc, TripSort.distance, TripSort.distance_desc
    #     (по убыванию – DESC; при равных значениях – по номеру: ..., id или ..., id DESC)
}


def not_found(trip_id: int) -> HTTPException:
    return HTTPException(status_code=404, detail=f"Поездки с номером {trip_id} нет")


# ---------------------------------------------------------------- Готовые маршруты

@app.get("/api/health", tags=["Служебное"], summary="Связь с базой данных")
def health(conn: Conn) -> dict:
    """Проверяет, что приложение подключается к базе: версия сервера, база и пользователь (З1, З4)."""
    row = conn.execute("SELECT version() AS version, current_database() AS database, current_user AS user").fetchone()
    return {"database": row["database"], "user": row["user"], "server": row["version"].split(",")[0]}


@app.get("/api/surfaces", tags=["Покрытия"], summary="Список покрытий")
def list_surfaces() -> list[dict]:
    """Четыре типа покрытия: код, название и учебный коэффициент сцепления."""
    return [{"code": code, "name": name, "mu": SURFACE_MU[code]} for code, name in SURFACE_NAMES.items()]


# ---------------------------------------------------------------- З5. Поездки в базе данных

@app.get("/api/trips", response_model=list[TripOut], tags=["Поездки"], summary="Список поездок")
def list_trips(
    conn: Conn,
    surface: Annotated[Surface | None, Query(description="Только поездки по этому покрытию")] = None,
    min_distance: Annotated[float, Query(ge=0, description="Только поездки не короче, км")] = 0,
    sort: Annotated[TripSort, Query(description="Порядок: id, date, -date, distance, -distance")] = TripSort.id,
):
    """Возвращает поездки из таблицы trips с фильтрами и сортировкой."""
    # <-- условия: список ["distance >= %(min_distance)s"] и словарь параметров {"min_distance": ...};
    #     если surface задан, добавить условие "surface = %(surface)s" и параметр.
    #     Текст запроса: f"SELECT {TRIP_COLUMNS} FROM trips WHERE ... ORDER BY {ORDER_BY[sort]}"
    #     (условия соединить через " AND "); вернуть conn.execute(запрос, параметры).fetchall()
    raise NotImplementedError("З5: list_trips")


@app.post("/api/trips", status_code=201, response_model=TripOut, tags=["Поездки"], summary="Добавить поездку")
def create_trip(trip: TripIn, conn: Conn, request: Request, response: Response):
    """Добавляет поездку одной командой INSERT ... RETURNING: база сама выдает номер и время создания."""
    # <-- row = conn.execute("""INSERT INTO trips (date, distance, surface, note, client_host)
    #                            VALUES (%(date)s, ...) RETURNING {TRIP_COLUMNS}""",
    #                        {**trip.model_dump(), "client_host": ...}).fetchone()
    #     заголовок Location, как в Т4.Б1.3, по row["id"]; вернуть row
    raise NotImplementedError("З5: create_trip")


# Маршрут /api/trips/summary объявлен ДО /api/trips/{trip_id}: FastAPI проверяет маршруты по порядку,
# и иначе слово summary попало бы в trip_id и получило бы ответ 422 «должно быть целым числом».
@app.get("/api/trips/summary", response_model=list[SurfaceSummary], tags=["Поездки"],
         summary="Сводка по покрытиям")
def trips_summary(conn: Conn):
    """З6. Число поездок и средний пробег по каждому покрытию (GROUP BY), по коду покрытия."""
    # <-- SELECT surface, COUNT(*) AS trips, ROUND(AVG(distance), 1) AS avg_distance ... GROUP BY ... ORDER BY ...
    raise NotImplementedError("З6: trips_summary")


@app.get("/api/trips/{trip_id}", response_model=TripOut, tags=["Поездки"], summary="Поездка по номеру",
         responses=NOT_FOUND)
def get_trip(trip_id: TripId, conn: Conn):
    """Возвращает одну поездку."""
    # <-- SELECT {TRIP_COLUMNS} FROM trips WHERE id = %s с параметром [trip_id]; .fetchone();
    #     нет строки (None) – raise not_found(trip_id)
    raise NotImplementedError("З5: get_trip")


@app.put("/api/trips/{trip_id}", response_model=TripOut, tags=["Поездки"], summary="Заменить поездку",
         responses=NOT_FOUND)
def replace_trip(trip_id: TripId, trip: TripIn, conn: Conn):
    """Заменяет данные поездки командой UPDATE ... RETURNING. Номер и время создания не меняются."""
    # <-- UPDATE trips SET date = %(date)s, distance = ..., surface = ..., note = ... WHERE id = %(id)s
    #     RETURNING {TRIP_COLUMNS}; параметры {**trip.model_dump(), "id": trip_id}; нет строки – 404
    raise NotImplementedError("З5: replace_trip")


@app.delete("/api/trips/{trip_id}", status_code=204, tags=["Поездки"], summary="Удалить поездку",
            responses=NOT_FOUND)
def delete_trip(trip_id: TripId, conn: Conn):
    """Удаляет поездку. cursor.rowcount – сколько строк удалила команда: 0 значит, поездки не было."""
    # <-- cursor = conn.execute("DELETE FROM trips WHERE id = %s", [trip_id]);
    #     cursor.rowcount == 0 – 404; иначе вернуть Response(status_code=204)
    raise NotImplementedError("З5: delete_trip")


# ---------------------------------------------------------------- Повышенная сложность

# <-- Маршрут GET /api/cars с response_model=list[CarOut]: автомобили с числом поездок и общим пробегом.
#     FROM cars AS c LEFT JOIN trips AS t ON t.car_id = c.id, GROUP BY c.id, ORDER BY c.id;
#     COUNT(t.id) AS trips, COALESCE(SUM(t.distance), 0) AS total_distance.


# ---------------------------------------------------------------- Единый формат ошибки (готово из Т4.Б1.3)

@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if is_json_error(errors):
        return JSONResponse({"error": NOT_JSON, "field": None}, status_code=400)
    problems = describe_all(errors)
    return JSONResponse({"error": problems[0]["error"], "field": problems[0]["field"], "errors": problems},
                        status_code=422)


@app.exception_handler(StarletteHTTPException)
def http_error_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse({"error": http_error_text(exc.detail, request.method), "field": None},
                        status_code=exc.status_code, headers=exc.headers)


# ---------------------------------------------------------------- Политика CORS (готово из Т4.Б1.3)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
    expose_headers=["Location"],
)
