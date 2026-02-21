import sys
from django.apps import AppConfig

class PersonalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personal'

    def ready(self):
        # Esta validación evita que el reloj arranque mientras DigitalOcean construye la app.
        # Solo arrancará cuando la página web esté viva y funcionando.
        if 'manage.py' not in sys.argv[0]:
            from . import scheduler
            try:
                scheduler.start()
            except Exception as e:
                print(f"Error iniciando scheduler: {e}")