import json
import time
import urllib.error
import urllib.request
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from .models import AnioFestivos, Festivo

URL_API = 'https://date.nager.at/api/v3/PublicHolidays/{anio}/CO'
TIEMPO_ESPERA = 8             # segundos que se espera a la API
VIGENCIA_DIAS = 30            # edad máxima de la copia de un año actual o futuro
MEMORIA_SEGUNDOS = 3600       # cuánto se recuerda un año en memoria antes de volver a mirar la base de datos

_memoria = {}                 # año -> (momento, frozenset de fechas)


class FestivosNoDisponibles(Exception):
    """La API no respondió y no hay una copia guardada de ese año."""


def _descargar(anio):
    """[(fecha, nombre)] de la API para ese año."""
    url = URL_API.format(anio=int(anio))
    if not url.startswith('https://'):         # solo https: urlopen también abriría file:// u otros esquemas
        raise FestivosNoDisponibles(f'La dirección de festivos debe ser https: {url}')
    peticion = urllib.request.Request(url, headers={'User-Agent': 'SYMA-PRO'})
    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_ESPERA) as respuesta:  # nosec B310: esquema https verificado arriba
            datos = json.load(respuesta)
        festivos = [(date.fromisoformat(f['date']), f.get('localName') or f.get('name') or '') for f in datos]
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, TypeError) as error:
        raise FestivosNoDisponibles(f'No se pudieron obtener los festivos de {anio}: {error}') from error
    if not festivos:
        raise FestivosNoDisponibles(f'La API no devolvió festivos para {anio}.')
    return festivos


def sincronizar_festivos(anio):
    """Descarga los festivos del año y reemplaza la copia guardada. Devuelve cuántos guardó."""
    festivos = _descargar(anio)
    with transaction.atomic():
        Festivo.objects.filter(fecha__year=anio).delete()
        Festivo.objects.bulk_create([Festivo(fecha=f, nombre=nombre) for f, nombre in festivos])
        AnioFestivos.objects.update_or_create(anio=anio, defaults={'actualizado_en': timezone.now()})
    _memoria.pop(anio, None)
    return len(festivos)


def festivos_colombia(anio):
    ahora = time.monotonic()
    recordado = _memoria.get(anio)
    if recordado and ahora - recordado[0] < MEMORIA_SEGUNDOS:
        return recordado[1]

    copia = AnioFestivos.objects.filter(anio=anio).first()
    desactualizada = copia is None or (
        anio >= date.today().year and timezone.now() - copia.actualizado_en > timedelta(days=VIGENCIA_DIAS)
    )
    if desactualizada:
        try:
            sincronizar_festivos(anio)
        except FestivosNoDisponibles:
            if copia is None:
                raise              # sin copia no hay con qué responder; con copia vieja se sigue usando

    fechas = frozenset(Festivo.objects.filter(fecha__year=anio).values_list('fecha', flat=True))
    _memoria[anio] = (ahora, fechas)
    return fechas


def es_festivo(d):
    return d in festivos_colombia(d.year)
