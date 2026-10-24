from datetime import date

from django.core.management.base import BaseCommand, CommandError

from registro_asistencia.festivos import FestivosNoDisponibles, sincronizar_festivos


class Command(BaseCommand):
    help = "Descarga de la API los festivos de Colombia (por defecto, el año actual y el siguiente)."

    def add_arguments(self, parser):
        parser.add_argument('anios', nargs='*', type=int, help='Años a descargar, por ejemplo 2026 2027')

    def handle(self, *args, **opciones):
        hoy = date.today().year
        for anio in opciones['anios'] or [hoy, hoy + 1]:
            try:
                total = sincronizar_festivos(anio)
            except FestivosNoDisponibles as error:
                raise CommandError(str(error))
            self.stdout.write(self.style.SUCCESS(f"{anio}: {total} festivos guardados"))
