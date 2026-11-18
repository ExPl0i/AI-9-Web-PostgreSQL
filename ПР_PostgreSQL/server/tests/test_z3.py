"""З3. Схема schema.sql и создание таблиц: python -m app.init_db."""

import psycopg
import pytest

from app import init_db
from app.config import BASE_DIR, settings
from conftest import TEST_URL, run_file

EXPECTED = {
    #  столбец      тип                         пусто нельзя  по умолчанию
    "id":          ("integer",                  "NO",  None),
    "date":        ("date",                     "NO",  None),
    "distance":    ("numeric",                  "NO",  None),
    "surface":     ("text",                     "NO",  None),
    "note":        ("text",                     "NO",  "''::text"),
    "created_at":  ("timestamp with time zone", "NO",  "now()"),
    "client_host": ("text",                     "YES", None),
}


def columns(url):
    with psycopg.connect(url) as conn:
        rows = conn.execute(
            """SELECT column_name, data_type, is_nullable, column_default, is_identity, identity_generation
               FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = 'trips'
               ORDER BY ordinal_position""").fetchall()
    return {r[0]: r[1:] for r in rows}


@pytest.fixture
def fresh():
    """Пустая тестовая база без таблицы trips; после теста схема восстанавливается."""
    with psycopg.connect(TEST_URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS trips, cars CASCADE")
    yield TEST_URL
    with psycopg.connect(TEST_URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS trips, cars CASCADE")
    run_file(TEST_URL, BASE_DIR / "schema.sql")


def test_create_tables(fresh):
    init_db.create_tables(fresh)
    cols = columns(fresh)
    assert cols, "после create_tables в базе нет таблицы trips"
    assert list(cols) == list(EXPECTED), f"столбцы {list(cols)}, ожидались {list(EXPECTED)} в этом порядке"
    for name, (data_type, nullable, default) in EXPECTED.items():
        got = cols[name]
        assert got[0] == data_type, f"{name}: тип {got[0]}, ожидался {data_type}"
        assert got[1] == nullable, f"{name}: " + ("нужно NOT NULL" if nullable == "NO" else "может быть пустым")
        assert got[2] == default, f"{name}: значение по умолчанию {got[2]}, ожидалось {default}"


def test_identity(fresh):
    init_db.create_tables(fresh)
    _, _, _, is_identity, generation = columns(fresh)["id"]
    assert is_identity == "YES" and generation == "ALWAYS", "номер: integer GENERATED ALWAYS AS IDENTITY"
    with psycopg.connect(fresh) as conn:
        pk = conn.execute(
            """SELECT a.attname FROM pg_index i
               JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
               WHERE i.indrelid = 'trips'::regclass AND i.indisprimary""").fetchall()
    assert pk == [("id",)], "первичный ключ – столбец id"


def test_defaults(fresh):
    init_db.create_tables(fresh)
    with psycopg.connect(fresh) as conn:
        row = conn.execute("""INSERT INTO trips (date, distance, surface) VALUES ('2026-11-05', 12.5, 'wet')
                              RETURNING id, note, created_at, client_host""").fetchone()
        conn.rollback()
    assert row[0] == 1 and row[1] == "" and row[2] is not None and row[3] is None


def test_can_run_twice(fresh):
    init_db.create_tables(fresh)
    with psycopg.connect(fresh) as conn:
        conn.execute("INSERT INTO trips (date, distance, surface) VALUES ('2026-11-05', 1, 'dry')")
    init_db.create_tables(fresh)
    with psycopg.connect(fresh) as conn:
        assert conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0] == 1, \
            "повторный запуск не должен удалять данные и падать: CREATE TABLE IF NOT EXISTS"


def test_main_database_ready():
    with psycopg.connect(settings.database_url) as conn:
        exists = conn.execute("SELECT to_regclass('public.trips') IS NOT NULL").fetchone()[0]
    assert exists, "в рабочей базе pokrytie нет таблицы trips: выполните python -m app.init_db"
