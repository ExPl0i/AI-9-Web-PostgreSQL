@echo off
chcp 65001 > nul
rem Т4.Б1.4, вариант А. Создание кластера PostgreSQL – папки с данными сервера. Выполняется один раз.
rem Кодировка UTF-8, встроенная локаль C.UTF-8, вход только по паролю. Скрипт спросит пароль суперпользователя postgres.
call "%~dp0db_env.bat"
if exist "%PGDATA%\PG_VERSION" (
  echo Папка данных %PGDATA% уже есть. Чтобы начать заново, остановите сервер, удалите папку и запустите скрипт еще раз.
  exit /b 1
)
"%PGBIN%\initdb" -D "%PGDATA%" -U postgres -E UTF8 --locale-provider=builtin --builtin-locale=C.UTF-8 -A scram-sha-256 -W
