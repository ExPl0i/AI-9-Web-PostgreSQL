-- Т4.Б1.4, задание З2. Архив поездок автопарка беспилотных автомобилей: 40 поездок за октябрь 2026 года.
-- Загрузка (таблица создается заново):  psql -U pokrytie -d pokrytie -f data/archive.sql

DROP TABLE IF EXISTS archive_trips;

CREATE TABLE archive_trips (
    id        integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    car       text    NOT NULL,   -- бортовой номер автомобиля
    date      date    NOT NULL,   -- дата поездки
    distance  numeric NOT NULL,   -- расстояние, км
    surface   text    NOT NULL,   -- покрытие: dry, wet, dirt, snow
    avg_speed numeric NOT NULL,   -- средняя скорость, км/ч
    rain      boolean NOT NULL,   -- шел ли дождь
    model_ok  boolean NOT NULL    -- совпал ли прогноз модели с настоящим покрытием
);

INSERT INTO archive_trips (car, date, distance, surface, avg_speed, rain, model_ok) VALUES
    ('АВ-01', '2026-10-01', 24.3, 'dry', 68.3, false, true),
    ('АВ-02', '2026-10-01', 11.0, 'dry', 70.4, false, true),
    ('АВ-03', '2026-10-01', 26.5, 'snow', 43.5, false, true),
    ('АВ-04', '2026-10-02', 28.3, 'snow', 31.8, false, true),
    ('АВ-01', '2026-10-02', 39.3, 'dry', 66.8, false, true),
    ('АВ-02', '2026-10-02', 32.7, 'dirt', 34.0, true, true),
    ('АВ-03', '2026-10-07', 12.3, 'wet', 49.5, true, false),
    ('АВ-04', '2026-10-03', 16.6, 'dry', 69.4, false, true),
    ('АВ-01', '2026-10-03', 42.1, 'wet', 59.9, true, true),
    ('АВ-02', '2026-10-04', 34.2, 'dry', 64.7, false, true),
    ('АВ-03', '2026-10-04', 28.3, 'wet', 55.0, true, false),
    ('АВ-04', '2026-10-04', 36.1, 'wet', 57.4, true, true),
    ('АВ-01', '2026-10-05', 12.7, 'snow', 36.1, false, true),
    ('АВ-02', '2026-10-05', 25.1, 'wet', 43.6, true, true),
    ('АВ-03', '2026-10-05', 2.7, 'dry', 72.9, false, true),
    ('АВ-04', '2026-10-06', 30.0, 'dry', 67.3, false, true),
    ('АВ-01', '2026-10-06', 42.6, 'dry', 71.0, false, true),
    ('АВ-02', '2026-10-06', 44.6, 'wet', 66.7, true, true),
    ('АВ-03', '2026-10-07', 0.6, 'dry', 22.0, false, true),
    ('АВ-04', '2026-10-07', 23.2, 'wet', 64.2, true, true),
    ('АВ-01', '2026-10-07', 13.2, 'dry', 56.8, false, true),
    ('АВ-02', '2026-10-08', 22.2, 'dirt', 41.5, false, true),
    ('АВ-03', '2026-10-08', 23.5, 'dry', 68.3, false, true),
    ('АВ-04', '2026-10-08', 27.0, 'snow', 47.8, false, true),
    ('АВ-01', '2026-10-09', 44.0, 'dry', 58.4, false, true),
    ('АВ-02', '2026-10-09', 24.9, 'snow', 36.9, false, true),
    ('АВ-03', '2026-10-09', 40.5, 'snow', 37.5, false, false),
    ('АВ-04', '2026-10-10', 24.1, 'dry', 58.3, false, true),
    ('АВ-01', '2026-10-10', 21.8, 'wet', 43.3, true, false),
    ('АВ-02', '2026-10-10', 44.8, 'wet', 45.0, true, true),
    ('АВ-03', '2026-10-11', 30.0, 'dry', 74.0, false, true),
    ('АВ-04', '2026-10-11', 30.6, 'dirt', 32.7, true, true),
    ('АВ-01', '2026-10-11', 45.6, 'snow', 37.8, false, true),
    ('АВ-02', '2026-10-12', 11.0, 'dry', 70.1, false, true),
    ('АВ-03', '2026-10-12', 24.4, 'snow', 28.0, false, true),
    ('АВ-04', '2026-10-12', 37.7, 'snow', 48.0, false, true),
    ('АВ-01', '2026-10-13', 38.9, 'wet', 55.5, true, true),
    ('АВ-02', '2026-10-13', 5.5, 'dry', 77.3, false, true),
    ('АВ-03', '2026-10-13', 17.2, 'wet', 61.5, true, false),
    ('АВ-04', '2026-10-14', 16.0, 'wet', 50.3, true, true);
