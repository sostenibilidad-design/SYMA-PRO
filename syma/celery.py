import os
from celery import Celery

# Establece el módulo de configuración de Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syma.settings')

app = Celery('syma')

# Lee la configuración desde settings.py usando el prefijo 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubre automáticamente los archivos tasks.py en todas tus apps instaladas
app.autodiscover_tasks()