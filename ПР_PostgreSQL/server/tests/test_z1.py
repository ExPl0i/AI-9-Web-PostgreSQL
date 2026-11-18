"""З1. Сервер PostgreSQL, роль pokrytie, базы pokrytie и pokrytie_test, файл .env."""

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.config import BASE_DIR, ENV_FILE, settings
from app.db import get_conn

HINT = ("не удалось подключиться к PostgreSQL. Сервер запущен (db\\db_start.bat или docker compose up -d)? "
        "Роль и базы созданы скриптом db/setup.sql? Пароль в .env совпадает с паролем роли?")


def connect(url):
    try:
        return psycopg.connect(url, connect_timeout=5)
    except psycopg.OperationalError as error:
        pytest.fail(f"{HINT}\nОшибка: {error}")


def test_env_file():
    assert ENV_FILE.exists(), "создайте файл server/.env по образцу .env.example"
    assert (BASE_DIR / ".env.example").exists(), "образец .env.example должен остаться в проекте"


def test_env_not_in_git():
    ignored = (BASE_DIR / ".gitignore").read_text(encoding="utf-8").split()
    assert ".env" in ignored, "файл .env с паролем не должен попасть в Git: строка .env в .gitignore"


def test_example_has_no_real_password():
    example = (BASE_DIR / ".env.example").read_text(encoding="utf-8")
    password = settings.database_url.split("@")[0].rsplit(":", 1)[-1]
    assert password and password not in example, \
        "пароль в .env совпадает с заглушкой из .env.example: задайте свой пароль (и в роли pokrytie тоже)"


def test_urls():
    assert settings.database_url.startswith("postgresql://pokrytie:")
    assert settings.database_url.endswith("/pokrytie")
    assert settings.test_database_url.endswith("/pokrytie_test")


@pytest.mark.parametrize("name, database", [("database_url", "pokrytie"), ("test_database_url", "pokrytie_test")])
def test_connect(name, database):
    with connect(getattr(settings, name)) as conn:
        user, db, version = conn.execute(
            "SELECT current_user, current_database(), current_setting('server_version_num')::int").fetchone()
    assert user == "pokrytie", "приложение подключается от имени роли pokrytie, а не суперпользователя postgres"
    assert db == database
    assert version >= 180000, f"в курсе используется PostgreSQL 18, а запущен сервер версии {version // 10000}"


def test_health_route():
    import app.main as main

    def test_conn():
        with psycopg.connect(settings.test_database_url, row_factory=dict_row) as conn:
            yield conn

    main.app.dependency_overrides[get_conn] = test_conn
    try:
        with TestClient(main.app) as client:
            r = client.get("/api/health")
    finally:
        main.app.dependency_overrides.clear()
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["database"] == "pokrytie_test" and body["user"] == "pokrytie"
    assert body["server"].startswith("PostgreSQL")
