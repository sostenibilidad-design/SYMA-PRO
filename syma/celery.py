import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syma.settings')

# Inyectamos la URL directamente en la creación para evitar que falle
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app = Celery('syma', broker=broker_url)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()