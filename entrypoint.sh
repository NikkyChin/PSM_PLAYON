#!/bin/sh

set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Iniciando Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 PSM_PLAYON.wsgi:application