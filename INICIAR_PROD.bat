@echo off
cd /d C:\Users\psmra\PSM_PLAYON_PROD

call entorno_virtual\Scripts\activate.bat

set DJANGO_DB_NAME=db_prod.sqlite3

python manage.py migrate

python manage.py runserver 127.0.0.1:8000

pause