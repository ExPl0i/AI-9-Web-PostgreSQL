"""З2. Повторение SQL: десять запросов к архиву поездок, файлы sql/q01.sql–sql/q10.sql."""

import psycopg
import pytest

from app.config import BASE_DIR, settings

EXPECTED = {
    "q01": (["id", "date", "distance"],
            [("4", "2026-10-02", "28.3"), ("24", "2026-10-08", "27.0"), ("36", "2026-10-12", "37.7")]),
    "q02": (["id", "car", "distance"],
            [("33", "АВ-01", "45.6"), ("30", "АВ-02", "44.8"), ("18", "АВ-02", "44.6"),
             ("25", "АВ-01", "44.0"), ("17", "АВ-01", "42.6")]),
    "q03": (["id", "car", "avg_speed"],
            [("18", "АВ-02", "66.7"), ("20", "АВ-04", "64.2"), ("39", "АВ-03", "61.5")]),
    "q04": (["id", "date", "car"],
            [("1", "2026-10-01", "АВ-01"), ("2", "2026-10-01", "АВ-02"), ("3", "2026-10-01", "АВ-03"),
             ("4", "2026-10-02", "АВ-04"), ("5", "2026-10-02", "АВ-01"), ("6", "2026-10-02", "АВ-02"),
             ("8", "2026-10-03", "АВ-04"), ("9", "2026-10-03", "АВ-01")]),
    "q05": (["surface", "trips"], [("dirt", "3"), ("dry", "16"), ("snow", "9"), ("wet", "12")]),
    "q06": (["car", "avg_distance"], [("АВ-01", "32.5"), ("АВ-04", "27.0"), ("АВ-02", "25.6"), ("АВ-03", "20.6")]),
    "q07": (["surface", "avg_speed"], [("dirt", "36.1"), ("snow", "38.6")]),
    "q08": (["surface", "error_percent"], [("dirt", "0.0"), ("dry", "0.0"), ("snow", "11.1"), ("wet", "33.3")]),
    "q09": (["id", "surface"], [("7", "snow"), ("19", "snow")]),
    "q10": (["id", "distance"], [("19", "0.6")]),
}
UNORDERED = {"q09", "q10"}   # у RETURNING порядок строк не задан, сравниваем без учета порядка


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_query(archive, name):
    path = BASE_DIR / "sql" / f"{name}.sql"
    text = path.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("--")).strip()
    assert code, f"{path.name}: напишите запрос (сейчас в файле только комментарий)"
    columns, rows = EXPECTED[name]
    with psycopg.connect(settings.test_database_url) as conn:
        try:
            cur = conn.execute(code)
        except psycopg.Error as error:
            pytest.fail(f"{path.name}: PostgreSQL не выполнил запрос: {error}")
        got_columns = [c.name for c in cur.description] if cur.description else []
        got = [tuple(str(v) for v in row) for row in cur.fetchall()] if cur.description else []
        conn.rollback()   # UPDATE и DELETE из q09 и q10 не меняют архив для следующих запусков
    assert got_columns == columns, f"{path.name}: столбцы {got_columns}, ожидались {columns} (имена задает AS)"
    if name in UNORDERED:
        got, rows = sorted(got), sorted(rows)
    assert got == rows, f"{path.name}: получено {got}"
