web: gunicorn --workers 1 --threads 1 --timeout 600 syma.wsgi --log-file -
worker: celery -A syma worker -l info --pool=solo