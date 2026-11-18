"""З4. Зависимость get_conn: одно соединение на запрос, подтверждение и отмена изменений."""

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import db as db_module
from conftest import count_trips

INSERT = "INSERT INTO trips (date, distance, surface) VALUES ('2026-11-05', 5, 'dry')"


def test_yields_connection(real_db):
    gen = db_module.get_conn()
    conn = next(gen)
    assert isinstance(conn, psycopg.Connection), "get_conn должна выдавать (yield) соединение psycopg"
    assert conn.execute("SELECT 1 AS x").fetchone() == {"x": 1}, \
        "строки – словари: psycopg.connect(..., row_factory=dict_row)"
    assert conn.info.dbname == "pokrytie_test", "строка подключения берется из settings.database_url"
    with pytest.raises(StopIteration):
        next(gen)
    assert conn.closed, "после запроса соединение закрыто: блок with вокруг yield"


def test_commit_on_success(real_db):
    gen = db_module.get_conn()
    conn = next(gen)
    conn.execute(INSERT)
    assert count_trips(real_db) == 0, "пока запрос не закончен, другие соединения изменения не видят"
    with pytest.raises(StopIteration):
        next(gen)
    assert count_trips(real_db) == 1, "в конце запроса изменения подтверждаются (COMMIT)"


def test_rollback_on_error(real_db):
    gen = db_module.get_conn()
    conn = next(gen)
    conn.execute(INSERT)
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("ошибка в обработчике"))
    assert conn.closed
    assert count_trips(real_db) == 0, "при исключении изменения отменяются (ROLLBACK)"


def test_one_connection_per_request(real_db, monkeypatch):
    import app.main as main

    opened = []
    real_connect = psycopg.connect

    def spy(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        opened.append(conn)
        return conn

    monkeypatch.setattr(psycopg, "connect", spy)
    with TestClient(main.app) as client:
        for _ in range(3):
            assert client.get("/api/health").status_code == 200
        assert client.get("/api/surfaces").status_code == 200
    assert len(opened) == 3, \
        f"на 3 запроса к базе открыто {len(opened)} соединений: нужно ровно одно на запрос (psycopg.connect в get_conn)"
    assert all(conn.closed for conn in opened), "после ответа все соединения закрыты"
