from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery
from celery.signals import after_setup_task_logger
from celery.schedules import crontab

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syma.settings')

app = Celery('syma')

# Usar configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubrir tareas automáticamente en apps
app.autodiscover_tasks()

# Configurar logging de tareas para que se escriba en un archivo
@after_setup_task_logger.connect
def setup_task_logger(logger, **kwargs):
    handler = logging.FileHandler(r"C:\Users\ANLLY V\OneDrive\Documentos\Sistema_SYMA\project\logs\celery_tasks.log")
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
