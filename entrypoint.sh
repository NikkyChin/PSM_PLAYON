#!/bin/sh

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando Gunicorn..."
gunicorn PSM_PLAYON.wsgi:application --bind 0.0.0.0:8000 --workers 3