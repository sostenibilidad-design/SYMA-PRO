#!/bin/bash
# Aplicar migraciones pendientes
python manage.py migrate --noinput

# Arrancar el trabajador de Celery en segundo plano
celery -A syma worker --loglevel=info &

# Arrancar Gunicorn en primer plano
# Hilos (gthread): una petición lenta (PDF, Excel, Drive) ya no deja en fila a las demás. Procesos: 1 por defecto; para
# subirlos (si el servicio tiene memoria de sobra) basta la variable WEB_CONCURRENCY en Cloud Run, sin tocar el código.
exec gunicorn --bind 0.0.0.0:8080 --worker-class gthread --threads "${GUNICORN_THREADS:-8}" --timeout 600 syma.wsgi:application
