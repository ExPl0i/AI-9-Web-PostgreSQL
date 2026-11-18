"""З5. Программный интерфейс Т4.Б1.3 на PostgreSQL: те же ответы, данные – в таблице trips."""

import datetime

import pytest

from conftest import API, PUBLIC, SEED_TIME, TRIP, seed

NEW = {"date": "2026-11-06", "distance": 40, "surface": "snow", "note": "метель"}


def stored(db, trip_id):
    return db.execute("SELECT * FROM trips WHERE id = %s", [trip_id]).fetchone()


# ---------------------------------------------------------------- список

def test_empty_list(client):
    r = client.get(API)
    assert r.status_code == 200 and r.json() == []


def test_list(client, db):
    for surface in ("dry", "snow", "wet"):
        seed(db, surface=surface)
    body = client.get(API).json()
    assert [t["id"] for t in body] == [1, 2, 3]
    assert set(body[0]) == PUBLIC, "только поля TripOut: client_host из базы клиенту не отдается"
    assert body[0]["distance"] == 12.5, "numeric из базы приходит как Decimal, в JSON – число"
    assert datetime.datetime.fromisoformat(body[0]["created_at"]) == SEED_TIME


# ---------------------------------------------------------------- создание

def test_create(client, db):
    r = client.post(API, json=TRIP)
    assert r.status_code == 201 and r.headers.get("location") == f"{API}/1"
    body = r.json()
    assert body["id"] == 1 and body["surface"] == "wet" and set(body) == PUBLIC
    created = datetime.datetime.fromisoformat(body["created_at"])
    assert created.tzinfo is not None, "время создания задает база (DEFAULT now(), тип timestamptz)"
    row = stored(db, 1)
    assert row is not None, "поездка записана в таблицу trips"
    assert row["client_host"] == "testclient" and row["note"] == TRIP["note"]


def test_create_without_note(client, db):
    trip = {k: v for k, v in TRIP.items() if k != "note"}
    assert client.post(API, json=trip).json()["note"] == ""
    assert stored(db, 1)["note"] == ""


def test_ids_not_reused(client, db):
    client.post(API, json=TRIP)
    client.post(API, json=TRIP)
    assert client.delete(f"{API}/2").status_code == 204
    assert client.post(API, json=TRIP).json()["id"] == 3, "номер выдает IDENTITY: удаленный номер не повторяется"


@pytest.mark.parametrize("change, field", [
    ({"distance": -5}, "distance"), ({"surface": "lava"}, "surface"), ({"date": "2026-02-30"}, "date"),
])
def test_create_wrong_422(client, db, change, field):
    r = client.post(API, json={**TRIP, **change})
    assert r.status_code == 422 and r.json()["field"] == field
    assert db.execute("SELECT COUNT(*) AS n FROM trips").fetchone()["n"] == 0


# ---------------------------------------------------------------- одна поездка

def test_get_one(client, db):
    seed(db)
    seed(db, surface="dirt")
    r = client.get(f"{API}/2")
    assert r.status_code == 200 and r.json()["surface"] == "dirt"


def test_get_missing(client):
    r = client.get(f"{API}/99")
    assert r.status_code == 404 and r.json() == {"error": "Поездки с номером 99 нет", "field": None}


def test_put(client, db):
    seed(db)
    r = client.put(f"{API}/1", json=NEW)
    assert r.status_code == 200
    body = r.json()
    assert body["surface"] == "snow" and body["distance"] == 40 and body["note"] == "метель"
    assert datetime.datetime.fromisoformat(body["created_at"]) == SEED_TIME, "время создания не меняется"
    row = stored(db, 1)
    assert row["surface"] == "snow" and row["date"] == datetime.date(2026, 11, 6), "UPDATE записал изменения в таблицу"


def test_put_missing(client):
    assert client.put(f"{API}/99", json=NEW).status_code == 404


def test_delete(client, db):
    seed(db)
    seed(db)
    r = client.delete(f"{API}/1")
    assert r.status_code == 204 and r.content == b""
    assert stored(db, 1) is None and stored(db, 2) is not None
    assert client.delete(f"{API}/1").status_code == 404


# ---------------------------------------------------------------- фильтры и сортировка

@pytest.fixture
def five(client, db):
    seed(db, date="2026-11-01", distance=12.5, surface="wet")
    seed(db, date="2026-11-03", distance=3.0, surface="snow")
    seed(db, date="2026-10-28", distance=40.0, surface="snow")
    seed(db, date="2026-11-02", distance=7.5, surface="dry")
    seed(db, date="2026-11-04", distance=21.0, surface="dirt")
    return client


@pytest.mark.parametrize("params, expected", [
    ({}, [1, 2, 3, 4, 5]),
    ({"surface": "snow"}, [2, 3]),
    ({"min_distance": 10}, [1, 3, 5]),
    ({"surface": "snow", "min_distance": 10}, [3]),
    ({"sort": "distance"}, [2, 4, 1, 5, 3]),
    ({"sort": "-distance"}, [3, 5, 1, 4, 2]),
    ({"sort": "date"}, [3, 1, 4, 2, 5]),
    ({"sort": "-date"}, [5, 2, 4, 1, 3]),
    ({"surface": "snow", "sort": "-distance"}, [3, 2]),
])
def test_filters_and_sort(five, params, expected):
    r = five.get(API, params=params)
    assert r.status_code == 200, r.text
    assert [t["id"] for t in r.json()] == expected, f"{params}"


def test_injection_is_just_a_value(five):
    r = five.get(API, params={"surface": "snow' OR '1'='1"})
    assert r.status_code == 422, "значение вне перечисления отклоняется еще до базы данных"
