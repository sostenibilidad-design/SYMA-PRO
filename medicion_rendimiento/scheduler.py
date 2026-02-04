from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .tasks import alerta_recordatorio_usuario, alerta_incumplimiento_control

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Alerta 1: 4:40 PM (16:40)
    scheduler.add_job(
        alerta_recordatorio_usuario,
        'cron',  # Tipo CRON (Hora específica)
        hour=16,
        minute=40,
        id='job_recordatorio_usuario',
        replace_existing=True,
    )

    # Alerta 2: 5:15 PM (17:15)
    scheduler.add_job(
        alerta_incumplimiento_control,
        'cron',  # Tipo CRON (Hora específica)
        hour=17,
        minute=15,
        id='job_alerta_control',
        replace_existing=True,
    )

    scheduler.start()
    print(">>> Scheduler SYMA: Alertas programadas para 16:40 y 17:15.")

"""
eliminar registros anteriores

python manage.py shell

from django_apscheduler.models import DjangoJob, DjangoJobExecution
# Borra todo el historial y las tareas programadas viejas
DjangoJobExecution.objects.all().delete()
DjangoJob.objects.all().delete()
exit()
"""