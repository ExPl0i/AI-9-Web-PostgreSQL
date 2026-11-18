rem Общие настройки скриптов варианта А. Поменяйте здесь, если PostgreSQL распакован в другую папку
rem или порт 5432 занят (тогда поставьте 5433 и поменяйте порт в строках подключения в .env).
set "PGBIN=%USERPROFILE%\pgsql\bin"
set "PGDATA=%USERPROFILE%\pgdata"
set "PGPORT=5432"
