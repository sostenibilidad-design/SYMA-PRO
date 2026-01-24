import os
import logging
from django.conf import settings
from celery import shared_task
from .google_drive_utils import fetch_and_store_empleados

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def fetch_empleados_task(self):
    root_folder_id = "1aN_dq95lckVrCo6NWMMqjRinV3XTkOCP"
    logger.info("Celery: Iniciando fetch_empleados_task")
    try:
        result = fetch_and_store_empleados(root_folder_id)
        logger.info(f"Celery: Resultado: {result}")
        return result
    except Exception as e:
        logger.exception(f"Celery: Error al ejecutar fetch_empleados_task: {e}")
        raise
