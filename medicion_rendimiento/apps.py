from django.apps import AppConfig

class MedicionRendimientoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medicion_rendimiento'

    def ready(self):
        import medicion_rendimiento.signals
