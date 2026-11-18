"""Повышенная сложность: таблица cars (sql/cars.sql) и GET /api/cars с JOIN. Запуск: pytest -m extra"""

import psycopg
import pytest

from app.config import BASE_DIR

pytestmark = pytest.mark.extra


@pytest.fixture
def cars(db):
    """Применяет sql/cars.sql внутри транзакции теста: в конце изменения схемы тоже отменяются."""
    db.execute((BASE_DIR / "sql" / "cars.sql").read_text(encoding="utf-8"))
    db.execute("INSERT INTO cars (plate, model) VALUES ('АВ-01', 'Модель Л'), ('АВ-02', 'Модель Л'), "
               "('АВ-03', 'Модель М')")
    return db


def test_cars_schema(cars):
    cols = {r["column_name"]: r for r in cars.execute(
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'cars'")}
    assert {"id", "plate", "model"} <= set(cols)
    fk = cars.execute(
        """SELECT ccu.table_name FROM information_schema.table_constraints tc
           JOIN information_schema.constraint_column_usage ccu USING (constraint_name)
           WHERE tc.table_name = 'trips' AND tc.constraint_type = 'FOREIGN KEY'""").fetchall()
    assert [r["table_name"] for r in fk] == ["cars"], "trips.car_id – внешний ключ на cars(id)"


def test_foreign_key_checked(cars):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        cars.execute("INSERT INTO trips (date, distance, surface, car_id) VALUES ('2026-11-05', 1, 'dry', 99)")


def test_cars_route(client, cars):
    cars.execute("""INSERT INTO trips (date, distance, surface, car_id) VALUES
                    ('2026-11-05', 12.5, 'wet', 1), ('2026-11-06', 40, 'snow', 1), ('2026-11-06', 3, 'dry', 2),
                    ('2026-11-07', 5, 'dry', NULL)""")
    r = client.get("/api/cars")
    assert r.status_code == 200, r.text
    assert r.json() == [
        {"id": 1, "plate": "АВ-01", "model": "Модель Л", "trips": 2, "total_distance": 52.5},
        {"id": 2, "plate": "АВ-02", "model": "Модель Л", "trips": 1, "total_distance": 3.0},
        {"id": 3, "plate": "АВ-03", "model": "Модель М", "trips": 0, "total_distance": 0.0},
    ], "LEFT JOIN оставляет автомобиль без поездок; COUNT(t.id) и COALESCE(SUM(...), 0)"
