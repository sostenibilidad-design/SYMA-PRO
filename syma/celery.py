# syma/celery.py
import os
from celery import Celery
from celery.schedules import crontab # Importar crontab

# Establecer el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syma.settings')

app = Celery('syma')

# Usar la configuración de settings.py con el prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodetectar tareas en las apps instaladas
app.autodiscover_tasks()

# === PROGRAMACIÓN DE TAREAS (BEAT) ===
app.conf.beat_schedule = {
    'alerta-recordatorio-5pm': {
        'task': 'medicion_rendimiento.tasks.alerta_recordatorio_usuario',
        'schedule': crontab(hour=17, minute=0), # 5:00 PM
    },
    'alerta-incumplimiento-515pm': {
        'task': 'medicion_rendimiento.tasks.alerta_incumplimiento_control',
        'schedule': crontab(hour=17, minute=15), # 5:15 PM
    },
}