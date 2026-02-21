import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events

from personal.google_drive_utils import fetch_and_store_empleados
from medicion_rendimiento.tasks import alerta_recordatorio_usuario, alerta_incumplimiento_control

logger = logging.getLogger(__name__)

def scheduled_fetch():
    try:
        logger.info("APScheduler: Iniciando sincronización automática de empleados...")
        result = fetch_and_store_empleados("1aN_dq95lckVrCo6NWMMqjRinV3XTkOCP")
        logger.info(f"APScheduler: Sincronización completada: {result}")
    except Exception as e:
        logger.exception(f"APScheduler: Error durante la sincronización: {e}")

def start():
    # Usamos la zona horaria de Colombia para que las horas coincidan perfecto
    scheduler = BackgroundScheduler(timezone="America/Bogota")
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # 1. Alerta Recordatorio: 4:40 PM (16:40) todos los días
    scheduler.add_job(
        alerta_recordatorio_usuario,
        trigger=CronTrigger(hour=16, minute=40),
        id='job_recordatorio_usuario',
        replace_existing=True,
    )

    # 2. Alerta Control: 5:15 PM (17:15) todos los días
    scheduler.add_job(
        alerta_incumplimiento_control,
        trigger=CronTrigger(hour=17, minute=15),
        id='job_alerta_control',
        replace_existing=True,
    )

    # 3. Google Drive: Días 3 y 17 de cada mes a las 08:00 AM
    scheduler.add_job(
        scheduled_fetch,
        trigger=CronTrigger(day="3,17", hour=8, minute=0),
        id="fetch_empleados_job",
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()
    print(">>> ⏰ Motor APScheduler encendido: Todas las tareas programadas listas.")