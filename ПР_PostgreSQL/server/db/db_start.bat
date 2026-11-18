@echo off
chcp 65001 > nul
rem Т4.Б1.4, вариант А. Запуск сервера PostgreSQL перед занятием. Журнал сервера – в файле server.log папки данных.
call "%~dp0db_env.bat"
"%PGBIN%\pg_ctl" -D "%PGDATA%" -l "%PGDATA%\server.log" -o "-p %PGPORT%" start
