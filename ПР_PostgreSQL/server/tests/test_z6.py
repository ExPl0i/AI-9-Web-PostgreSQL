"""З6. Сводка по покрытиям (GROUP BY) и сохранность данных после перезапуска приложения."""

import importlib

from fastapi.testclient import TestClient

from conftest import API, TRIP, count_trips, seed


def test_summary_empty(client):
    r = client.get(f"{API}/summary")
    assert r.status_code == 200, "адрес /api/trips/summary должен быть объявлен раньше /api/trips/{trip_id}"
    assert r.json() == []


def test_summary(client, db):
    seed(db, surface="snow", distance=3)
    seed(db, surface="snow", distance=40)
    seed(db, surface="snow", distance=10.4)
    seed(db, surface="dry", distance=7.5)
    seed(db, surface="wet", distance=12.5)
    seed(db, surface="wet", distance=12.6)
    r = client.get(f"{API}/summary")
    assert r.status_code == 200
    assert r.json() == [
        {"surface": "dry", "trips": 1, "avg_distance": 7.5},
        {"surface": "snow", "trips": 3, "avg_distance": 17.8},
        {"surface": "wet", "trips": 2, "avg_distance": 12.6},
    ], "COUNT(*) и ROUND(AVG(distance), 1) с GROUP BY surface, по коду покрытия"


def test_summary_in_docs(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert f"{API}/summary" in paths
    schema = paths[f"{API}/summary"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema.get("type") == "array" and schema["items"]["$ref"].endswith("/SurfaceSummary")


def test_data_survives_restart(real_db):
    import app.main as main

    with TestClient(main.app) as client:
        assert client.post(API, json=TRIP).status_code == 201
        assert client.post(API, json={**TRIP, "surface": "snow"}).status_code == 201
    assert count_trips(real_db) == 2, "после ответа 201 поездки уже подтверждены в базе"

    importlib.reload(main)   # «перезапуск»: модуль выполняется заново, переменные в памяти создаются с нуля
    with TestClient(main.app) as client:
        body = client.get(API).json()
    assert [t["surface"] for t in body] == ["wet", "snow"], "после перезапуска поездки на месте: они в PostgreSQL"
