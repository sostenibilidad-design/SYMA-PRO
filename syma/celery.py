import os
from celery import Celery
from celery.schedules import crontab

# Establecer el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syma.settings')

app = Celery('syma')

# Usar la configuración de settings.py con el prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Asegurar que Celery use la hora de Colombia
app.conf.timezone = 'America/Bogota'

# Autodetectar tareas en las apps instaladas
app.autodiscover_tasks()

# === PROGRAMACIÓN DE TAREAS (BEAT) ===
app.conf.beat_schedule = {
    # 1. Alerta de Recordatorio (4:40 PM)
    'alerta-recordatorio-1640pm': {
        'task': 'medicion_rendimiento.tasks.alerta_recordatorio_usuario',
        'schedule': crontab(hour=16, minute=40), 
    },
    # 2. Alerta de Control (5:15 PM)
    'alerta-incumplimiento-1715pm': {
        'task': 'medicion_rendimiento.tasks.alerta_incumplimiento_control',
        'schedule': crontab(hour=17, minute=15), 
    },
    # 3. Extracción de Empleados de Drive (Días 3 y 17 de cada mes a las 8:00 AM)
    'sincronizar-empleados-quincenal': {
        'task': 'personal.tasks.fetch_empleados_task',
        'schedule': crontab(day_of_month='3,17', hour=8, minute=0),
    }
}