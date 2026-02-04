from django.apps import AppConfig


class MedicionRendimientoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medicion_rendimiento'

    def ready(self):
        import medicion_rendimiento.signals
        # Importamos el scheduler aquí para evitar errores de carga
        from . import scheduler
        import os
        
        # El chequeo del RUN_MAIN es para evitar que el scheduler se ejecute 
        # dos veces cuando usas el auto-reload de Django (runserver)
        if os.environ.get('RUN_MAIN') == 'true':
            scheduler.start()
