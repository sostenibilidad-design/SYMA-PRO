#!/bin/bash
# Aplicar migraciones pendientes
python manage.py migrate --noinput

# Arrancar el trabajador de Celery en segundo plano
celery -A syma worker --loglevel=info &

# Arrancar Gunicorn en primer plano
exec gunicorn --bind 0.0.0.0:8080 --timeout 600 syma.wsgi:application