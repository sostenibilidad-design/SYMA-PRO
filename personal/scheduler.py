import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events

from .google_drive_utils import fetch_and_store_empleados

logger = logging.getLogger(__name__)

# --- función global que se ejecutará ---
def scheduled_fetch():
    try:
        logger.info("APScheduler: Iniciando sincronización de empleados...")
        result = fetch_and_store_empleados("1aN_dq95lckVrCo6NWMMqjRinV3XTkOCP")
        logger.info(f"APScheduler: Sincronización completada: {result}")
    except Exception as e:
        logger.exception(f"APScheduler: Error durante la sincronización: {e}")


def start():
    scheduler = BackgroundScheduler(timezone="America/Bogota")
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Ejecutar los días 3 y 17 de cada mes a las 08:00 a.m.
    scheduler.add_job(
        "personal.scheduler:scheduled_fetch",  # ← referencia textual
        trigger=CronTrigger(day="3,17", hour=8, minute=0),
        id="fetch_empleados_job",
        jobstore="default",
        replace_existing=True,
    )

    register_events(scheduler)
    scheduler.start()
    logger.info("APScheduler: iniciado correctamente.")