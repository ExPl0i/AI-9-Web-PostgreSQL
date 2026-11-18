@echo off
chcp 65001 > nul
rem Т4.Б1.4, вариант А. Остановка сервера PostgreSQL после занятия.
call "%~dp0db_env.bat"
"%PGBIN%\pg_ctl" -D "%PGDATA%" stop
