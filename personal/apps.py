from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class PersonalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personal'

    def ready(self):
        from django.conf import settings
        if settings.DEBUG:  # puedes quitar esta línea si quieres que corra también en producción
            try:
                from . import scheduler
                scheduler.start()
                logger.info("Scheduler iniciado desde PersonalConfig.ready()")
            except Exception as e:
                logger.exception(f"No se pudo iniciar el scheduler: {e}")
