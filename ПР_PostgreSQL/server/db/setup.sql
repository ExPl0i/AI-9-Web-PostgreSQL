-- Т4.Б1.4. Роль и базы данных сервиса «Покрытие» (вариант А: архив PostgreSQL без установки).
-- Выполняется один раз от имени суперпользователя postgres; пароль передается переменной psql:
--     psql -U postgres -v password=ваш_пароль -f db/setup.sql
-- Тот же пароль записывается в файл .env. Скрипт можно запускать повторно: то, что уже есть, не создается.

\set ON_ERROR_STOP on

-- Роль (пользователь) pokrytie: от ее имени подключается приложение.
SELECT format('CREATE ROLE pokrytie LOGIN PASSWORD %L', :'password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pokrytie')
\gexec

-- Рабочая база и база для тестов; владелец обеих – pokrytie.
SELECT 'CREATE DATABASE pokrytie OWNER pokrytie'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'pokrytie')
\gexec

SELECT 'CREATE DATABASE pokrytie_test OWNER pokrytie'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'pokrytie_test')
\gexec

\echo 'Готово: роль pokrytie, базы pokrytie и pokrytie_test.'
