@echo off
chcp 65001 > nul
rem Т4.Б1.4, вариант А. Роль pokrytie и базы pokrytie, pokrytie_test (скрипт setup.sql).
rem Запуск: db\db_setup.bat ваш_пароль   – пароль роли pokrytie, тот же, что в .env.
rem Скрипт спросит пароль суперпользователя postgres, заданный в db_init.bat.
if "%~1"=="" (
  echo Укажите пароль роли pokrytie: db\db_setup.bat ваш_пароль
  exit /b 1
)
call "%~dp0db_env.bat"
"%PGBIN%\psql" -h 127.0.0.1 -p %PGPORT% -U postgres -d postgres -v password=%1 -f "%~dp0setup.sql"
