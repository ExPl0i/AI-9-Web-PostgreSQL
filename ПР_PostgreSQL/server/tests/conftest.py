"""Общие помощники тестов. Этот файл писать не нужно, он готовый.

Тесты работают с тестовой базой pokrytie_test (строка TEST_DATABASE_URL в .env), рабочую базу не трогают.
Большинство тестов выполняются внутри транзакции, которая в конце отменяется (ROLLBACK):
после теста база остается такой же, как до него, и тесты не мешают друг другу.
"""

import datetime

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.config import BASE_DIR, settings
from app.db import get_conn

TEST_URL = settings.test_database_url
API = "/api/trips"
TRIP = {"date": "2026-11-05", "distance": 12.5, "surface": "wet", "note": "дождь после обеда"}
PUBLIC = {"id", "date", "distance", "surface", "note", "created_at"}
SEED_TIME = datetime.datetime(2026, 11, 5, 14, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=7)))


def run_file(url, path):
    """Выполняет SQL-файл целиком в базе url и подтверждает изменения."""
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def archive():
    """Архив поездок для задания З2: таблица archive_trips в тестовой базе, загружается один раз."""
    run_file(TEST_URL, BASE_DIR / "data" / "archive.sql")


@pytest.fixture(scope="session")
def schema():
    """Таблицы сервиса в тестовой базе: создаются заново по вашему schema.sql (задание З3)."""
    with psycopg.connect(TEST_URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS trips, cars CASCADE")
    run_file(TEST_URL, BASE_DIR / "schema.sql")


@pytest.fixture
def db(schema):
    """Соединение с тестовой базой внутри транзакции: таблица trips пустая, номера с 1, в конце ROLLBACK."""
    conn = psycopg.connect(TEST_URL, row_factory=dict_row)
    conn.execute("TRUNCATE trips RESTART IDENTITY CASCADE")
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def client(db):
    """Тестовый клиент: все запросы приложения идут через соединение db (подмена зависимости get_conn)."""
    import app.main as main

    def test_conn():
        yield db

    main.app.dependency_overrides[get_conn] = test_conn
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


@pytest.fixture
def real_db(schema, monkeypatch):
    """Для тестов З4 и З6: приложение само открывает соединения к тестовой базе, изменения подтверждаются.

    До и после теста таблица trips очищается отдельной командой.
    """
    monkeypatch.setattr(settings, "database_url", TEST_URL)
    clean = "TRUNCATE trips RESTART IDENTITY CASCADE"
    with psycopg.connect(TEST_URL, autocommit=True) as conn:
        conn.execute(clean)
    yield TEST_URL
    with psycopg.connect(TEST_URL, autocommit=True) as conn:
        conn.execute(clean)


def seed(db, **changes):
    """Кладет поездку прямо в таблицу trips командой INSERT (в обход POST). Возвращает номер."""
    data = {**TRIP, **changes}
    data["date"] = datetime.date.fromisoformat(data["date"])
    row = db.execute(
        """INSERT INTO trips (date, distance, surface, note, created_at, client_host)
           VALUES (%(date)s, %(distance)s, %(surface)s, %(note)s, %(created_at)s, '127.0.0.1')
           RETURNING id""",
        {**data, "created_at": SEED_TIME},
    ).fetchone()
    return row["id"]


def count_trips(url):
    """Сколько поездок в таблице, если смотреть из отдельного соединения (видны только подтвержденные)."""
    with psycopg.connect(url) as conn:
        return conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
