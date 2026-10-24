import json

from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Max, Min
from django.http import JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from personal.models import Empleado
from .festivos import FestivosNoDisponibles
from .liquidacion import ASISTENCIA, DESCANSO, RETIRO, dias_habiles, es_habil, minutos_efectivos
from .models import MaestroAsistencia, RegistroEntradaSalida
from .views import (
    TIPOS_COMIDA, aplicar_actualizacion, cedulas_con_historial, contexto_campos_registro, datos_quincena,
    dia_de_registro, permiso_registro, respuesta_comidas_habituales, validar_actualizacion,
)

DIAS_SEMANA = ('Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom')

# Novedad "anterior" de un registro que todavía no existe: con ella validar_actualizacion exige la actividad
# en las asistencias nuevas, igual que cuando alguien pasa a Asistencia desde otra novedad.
NOVEDAD_NUEVO_REGISTRO = 'Nuevo'

MENSAJE_ACTIVIDAD = 'La actividad es obligatoria en una asistencia.'

ERROR_FESTIVOS = 'No se pudo consultar el calendario de festivos y no hay una copia guardada. Intenta de nuevo en unos minutos.'

ERROR_NO_NUEVO = 'La fecha de ingreso solo se puede editar en empleados nuevos (con «Nuevo» en el informe).'


# ---------------------------------------------------------------------------
# Ayudantes
# ---------------------------------------------------------------------------

def fecha_o_none(texto):
    """'2026-10-02' -> date; None si está vacío o no se puede leer."""
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def texto_dia(fecha):
    """'Vie 02/10/2026'."""
    return f"{DIAS_SEMANA[fecha.weekday()]} {fecha:%d/%m/%Y}"


def dias_entre(desde, hasta):
    """Días desde `desde` hasta el día ANTES de `hasta`."""
    dias = []
    dia = desde
    while dia < hasta:
        dias.append(dia)
        dia += timedelta(days=1)
    return dias


def registros_del_empleado(proyecto, empleado, desde, hasta):
    """Registros guardados (días completados) del empleado entre dos fechas, ambas incluidas."""
    return RegistroEntradaSalida.objects.filter(
        maestro__proyecto=proyecto, maestro__estado='Completado',
        maestro__fecha__range=(desde, hasta), empleado=empleado,
    )


def maestros_completados(proyecto, desde, hasta):
    """{fecha: maestro} de los días del proyecto que ya tienen su registro guardado, entre dos fechas (ambas incluidas).

    Solo esos días se pueden editar: un día sin registro (por ejemplo un domingo que nadie registró) no se toca.
    """
    return {m.fecha: m for m in MaestroAsistencia.objects.filter(
        proyecto=proyecto, estado='Completado', fecha__range=(desde, hasta))}


def error_dia_sin_registro(proyecto, nueva):
    """Texto del error si la nueva fecha de ingreso es un día sin registro en el proyecto; None si tiene."""
    if nueva in maestros_completados(proyecto, nueva, nueva):
        return None
    return f'El {texto_dia(nueva)} no tiene registro en este proyecto, así que no se puede usar como ingreso. Elige un día con registro.'


def limites_del_ingreso(proyecto, empleado, inicio, fin):
    """(primer día, último día) que el empleado tiene registro en la quincena; (None, None) si no tiene."""
    fechas = registros_del_empleado(proyecto, empleado, inicio, fin).aggregate(
        primero=Min('maestro__fecha'), ultimo=Max('maestro__fecha'))
    return fechas['primero'], fechas['ultimo']


def error_si_no_es_nuevo(empleado, inicio, actual):
    """Respuesta de error (JSON) si el empleado no es nuevo; None si se le puede editar la fecha de ingreso.

    Es nuevo si (1) quedan días hábiles de la quincena antes de su primer registro, que es lo que muestra el informe
    como «Nuevo», y (2) no tiene ningún registro guardado antes de la quincena, en ningún proyecto.
    """
    if cedulas_con_historial(inicio, [empleado]):
        return JsonResponse({'success': False, 'error': ERROR_NO_NUEVO, 'errores': [ERROR_NO_NUEVO]}, status=403)
    try:
        quedan_dias_antes = any(True for _ in dias_habiles(inicio, actual - timedelta(days=1)))
    except FestivosNoDisponibles:
        return JsonResponse({'success': False, 'error': ERROR_FESTIVOS, 'errores': [ERROR_FESTIVOS]}, status=503)
    if not quedan_dias_antes:
        return JsonResponse({'success': False, 'error': ERROR_NO_NUEVO, 'errores': [ERROR_NO_NUEVO]}, status=403)
    return None


def error_nueva_fecha(nueva, actual, ultimo, inicio):
    """Texto del error si la nueva fecha no se puede usar; None si sirve."""
    if nueva is None:
        return 'Escribe una fecha válida.'
    if nueva == actual:
        return 'Es la misma fecha de ingreso que ya tiene. Elige otra.'
    if nueva < inicio:
        return f'La fecha debe estar dentro de la quincena (desde el {inicio:%d/%m/%Y}).'
    if nueva > ultimo:
        return f'La fecha no puede quedar después de su último día registrado ({ultimo:%d/%m/%Y}).'
    return None


def a_querydict(campos):
    """{'novedad': ['Asistencia'], 'mult_salida': ['10:00', ...]} -> QueryDict, el formato que espera validar_actualizacion."""
    datos = QueryDict(mutable=True)
    if isinstance(campos, dict):
        for nombre, valores in campos.items():
            if isinstance(valores, list):
                datos.setlist(nombre, [str(v) for v in valores])
    return datos


def contexto_empleado(id_proyecto, anio, mes, quincena, cedula):
    """Lo que necesitan todas las vistas: proyecto, rango de la quincena, empleado y su fecha de ingreso actual."""
    proyecto, inicio, fin = datos_quincena(id_proyecto, anio, mes, quincena)
    empleado = get_object_or_404(Empleado, pk=cedula)
    actual, ultimo = limites_del_ingreso(proyecto, empleado, inicio, fin)
    return proyecto, inicio, fin, empleado, actual, ultimo


def urls_del_empleado(id_proyecto, anio, mes, quincena, cedula):
    args = [id_proyecto, anio, mes, quincena, cedula]
    return {
        'url_revisar': reverse('fecha_ingreso_revisar', args=args),
        'url_comidas': reverse('fecha_ingreso_comidas', args=args),
        'url_agregar': reverse('fecha_ingreso_agregar', args=args),
        'url_eliminar': reverse('fecha_ingreso_eliminar', args=args),
    }


def sin_registros():
    return JsonResponse({'success': False, 'error': 'Este empleado no tiene registros en la quincena.'}, status=404)


# ---------------------------------------------------------------------------
# 1. Modal corto: elegir la nueva fecha
# ---------------------------------------------------------------------------

@permiso_registro('actualizar', json=True)
@require_GET
def fecha_ingreso(request, id_proyecto, anio, mes, quincena, cedula):
    """Modal con la fecha de ingreso actual y el campo para la nueva.

    Incluye, por cada día entre el inicio de la quincena y el último registro, si es hábil y qué novedad tiene,
    para que el JavaScript muestre antes de continuar qué días se van a agregar o a eliminar.
    """

    proyecto, inicio, fin, empleado, actual, ultimo = contexto_empleado(id_proyecto, anio, mes, quincena, cedula)
    if actual is None:
        return sin_registros()
    error = error_si_no_es_nuevo(empleado, inicio, actual)
    if error:
        return error

    novedades = dict(
        registros_del_empleado(proyecto, empleado, inicio, ultimo).values_list('maestro__fecha', 'novedad'))
    registrados = maestros_completados(proyecto, inicio, ultimo)
    try:
        dias = [
            {'iso': d.isoformat(), 'texto': texto_dia(d)[:-5], 'habil': es_habil(d), 'registrado': d in registrados,
             'novedad': novedades.get(d)}
            for d in dias_entre(inicio, ultimo + timedelta(days=1))
        ]
    except FestivosNoDisponibles:
        return JsonResponse({'success': False, 'error': ERROR_FESTIVOS}, status=503)

    context = {
        'empleado': empleado,
        'actual': actual,
        'actual_texto': texto_dia(actual),
        'inicio': inicio,
        'ultimo': ultimo,
        'dias': dias,
        **urls_del_empleado(id_proyecto, anio, mes, quincena, cedula),
    }
    return render(request, 'registro_asistencia/modal_fecha_ingreso.html', context)


# ---------------------------------------------------------------------------
# 2. Revisar: paso a paso (fecha anterior) o eliminación (fecha posterior)
# ---------------------------------------------------------------------------

@permiso_registro('actualizar', json=True)
@require_GET
def fecha_ingreso_revisar(request, id_proyecto, anio, mes, quincena, cedula):
    proyecto, inicio, fin, empleado, actual, ultimo = contexto_empleado(id_proyecto, anio, mes, quincena, cedula)
    if actual is None:
        return sin_registros()
    error = error_si_no_es_nuevo(empleado, inicio, actual)
    if error:
        return error
    nueva = fecha_o_none(request.GET.get('nueva'))
    error = error_nueva_fecha(nueva, actual, ultimo, inicio)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)

    if nueva < actual:
        error = error_dia_sin_registro(proyecto, nueva)
        if error:
            return JsonResponse({'success': False, 'error': error}, status=400)

    base = {
        'empleado': empleado,
        'actual': actual,
        'nueva': nueva,
        'nueva_texto': texto_dia(nueva),
        **urls_del_empleado(id_proyecto, anio, mes, quincena, cedula),
    }
    if nueva < actual:
        return modal_de_pasos(request, proyecto, base)
    return modal_de_eliminacion(request, proyecto, empleado, actual, nueva, ultimo, base)


def modal_de_pasos(request, proyecto, base):
    """Un paso por cada día que falta Y que ya tiene registro en el proyecto. Los días hábiles empiezan en Asistencia;
    sábados, domingos y festivos en Descanso. Los días sin registro no se editan: se avisan como omitidos."""
    registrados = maestros_completados(proyecto, base['nueva'], base['actual'] - timedelta(days=1))
    try:
        dias = [
            {
                'fecha': d, 'iso': d.isoformat(), 'texto': texto_dia(d), 'corto': f"{DIAS_SEMANA[d.weekday()]} {d:%d/%m}",
                'habil': es_habil(d),
            }
            for d in dias_entre(base['nueva'], base['actual']) if d in registrados
        ]
    except FestivosNoDisponibles:
        return JsonResponse({'success': False, 'error': ERROR_FESTIVOS}, status=503)
    omitidos = [texto_dia(d) for d in dias_entre(base['nueva'], base['actual']) if d not in registrados]

    for dia in dias:
        dia['novedad_inicial'] = ASISTENCIA if dia['habil'] else DESCANSO

    campos = contexto_campos_registro(proyecto)       # los mismos campos de «Actualizar registro»
    campos['novedades'] = [(v, n) for v, n in campos['novedades'] if v != RETIRO]     # nadie se retira antes de ingresar
    context = {
        **base,
        **campos,
        'dias': dias,
        'omitidos': omitidos,
        'comidas': [(tipo, tipo.capitalize(), None) for tipo in TIPOS_COMIDA],
    }
    return render(request, 'registro_asistencia/modal_pasos_ingreso.html', context)


def modal_de_eliminacion(request, proyecto, empleado, actual, nueva, ultimo, base):
    """Lista de los registros que se borrarán y en qué día queda el ingreso."""
    registros = (registros_del_empleado(proyecto, empleado, actual, nueva - timedelta(days=1))
                .select_related('maestro').prefetch_related('horas_multiples', 'horas_historicas')
                .order_by('maestro__fecha'))
    filas = [
        {
            'texto': texto_dia(r.maestro.fecha),
            'novedad': r.novedad,
            'horario': f"{r.hora_inicio:%H:%M} – {r.hora_fin:%H:%M}" if r.hora_inicio and r.hora_fin else '--',
            'horas': minutos_efectivos(dia_de_registro(r)) / 60 if r.novedad == ASISTENCIA else 0,
        }
        for r in registros
    ]
    # Si la nueva fecha no tiene registro, el ingreso queda en el siguiente día registrado
    queda = registros_del_empleado(proyecto, empleado, nueva, ultimo).aggregate(primero=Min('maestro__fecha'))['primero']
    context = {
        **base,
        'filas': filas,
        'queda_en': texto_dia(queda) if queda else None,
        'queda_distinta': queda != nueva,
    }
    return render(request, 'registro_asistencia/modal_eliminar_ingreso.html', context)


@permiso_registro('actualizar', json=True)
@require_GET
def fecha_ingreso_comidas(request, id_proyecto, anio, mes, quincena, cedula):
    """Comidas habituales que cruza un turno en un día (el paso a paso las rellena al escribir las horas)."""
    proyecto, _, _ = datos_quincena(id_proyecto, anio, mes, quincena)
    fecha = fecha_o_none(request.GET.get('fecha'))
    if fecha is None:
        return JsonResponse({'comidas': {}})
    return respuesta_comidas_habituales(proyecto, fecha, request.GET.get('entrada', ''), request.GET.get('salida', ''))


# ---------------------------------------------------------------------------
# 3. Guardar
# ---------------------------------------------------------------------------

def leer_cuerpo(request):
    """(cuerpo JSON, fecha nueva, fecha actual que vio el usuario); (None, None, None) si no se puede leer."""
    try:
        cuerpo = json.loads(request.body)
    except (ValueError, TypeError):
        return None, None, None
    if not isinstance(cuerpo, dict):
        return None, None, None
    return cuerpo, fecha_o_none(cuerpo.get('nueva')), fecha_o_none(cuerpo.get('actual'))


def bloquear_quincena(proyecto, inicio, fin):
    """Bloquea los días de la quincena hasta terminar la transacción: nadie más los cambia mientras se guarda."""
    list(MaestroAsistencia.objects.select_for_update().filter(proyecto=proyecto, fecha__range=(inicio, fin)))


ERROR_CAMBIO = 'La fecha de ingreso cambió mientras editabas (otra persona guardó cambios). Cierra y vuelve a abrir.'


@permiso_registro('actualizar', json=True)
@require_POST
def fecha_ingreso_agregar(request, id_proyecto, anio, mes, quincena, cedula):
    """Crea los registros de los días que faltan. O se guardan todos o ninguno.

    Cuerpo: {"nueva": "2026-10-02", "actual": "2026-10-05", "dias": {"2026-10-02": {"novedad": ["Asistencia"], ...}}}
    Cada día trae los mismos campos del modal «Actualizar registro» y se valida con las mismas reglas.
    """
    cuerpo, nueva, actual_visto = leer_cuerpo(request)
    if cuerpo is None or not isinstance(cuerpo.get('dias'), dict):
        return JsonResponse({'success': False, 'errores': ['Datos inválidos.']}, status=400)

    proyecto, inicio, fin = datos_quincena(id_proyecto, anio, mes, quincena)
    empleado = get_object_or_404(Empleado, pk=cedula)

    with transaction.atomic():
        bloquear_quincena(proyecto, inicio, fin)
        actual, ultimo = limites_del_ingreso(proyecto, empleado, inicio, fin)
        if actual is None or actual != actual_visto:
            return JsonResponse({'success': False, 'errores': [ERROR_CAMBIO]}, status=409)
        no_nuevo = error_si_no_es_nuevo(empleado, inicio, actual)
        if no_nuevo:
            return no_nuevo
        error = error_nueva_fecha(nueva, actual, ultimo, inicio)
        if error or nueva > actual:
            return JsonResponse({'success': False, 'errores': [error or 'La nueva fecha no es anterior a la actual.']}, status=400)

        # Solo se editan los días que ya tienen registro en el proyecto; los demás (p. ej. un domingo que nadie registró)
        # no se tocan ni se crean: en el informe ya cuentan como descanso.
        maestros = maestros_completados(proyecto, nueva, actual - timedelta(days=1))
        error = error_dia_sin_registro(proyecto, nueva)
        if error:
            return JsonResponse({'success': False, 'errores': [error]}, status=400)
        fechas = [f for f in dias_entre(nueva, actual) if f in maestros]
        if set(cuerpo['dias']) != {f.isoformat() for f in fechas}:
            return JsonResponse({'success': False, 'errores': ['Los días enviados no coinciden con los que tienen registro. Vuelve a abrir el paso a paso.']}, status=400)

        validados, errores, paso_con_error = [], [], None
        for indice, fecha in enumerate(fechas):
            datos, errs = validar_actualizacion(a_querydict(cuerpo['dias'][fecha.isoformat()]), NOVEDAD_NUEVO_REGISTRO)
            errs = [MENSAJE_ACTIVIDAD if e.startswith('Al pasar a Asistencia') else e for e in errs]
            if datos['novedad'] == RETIRO:
                errs.append('No se puede registrar un retiro antes de la fecha de ingreso.')
            if errs and paso_con_error is None:
                paso_con_error = indice
            errores += [f"{texto_dia(fecha)}: {e}" for e in errs]
            validados.append((maestros[fecha], datos))
        if errores:
            return JsonResponse({'success': False, 'errores': errores, 'paso': paso_con_error}, status=400)

        for maestro, datos in validados:
            registro = RegistroEntradaSalida(maestro=maestro, empleado=empleado, novedad=datos['novedad'])
            aplicar_actualizacion(registro, datos)     # guarda y recalcula jornada, comidas, múltiples e históricas
        guardados = len(validados)

    return JsonResponse({'success': True, 'guardados': guardados})


@permiso_registro('actualizar', json=True)
@permiso_registro('eliminar', json=True)
@require_POST
def fecha_ingreso_eliminar(request, id_proyecto, anio, mes, quincena, cedula):
    """Borra los registros del empleado desde la fecha actual hasta el día antes de la nueva. No se puede deshacer.

    Cuerpo: {"nueva": "2026-10-08", "actual": "2026-10-05"}. Solo se borran los registros de este empleado;
    las carpetas de esos días siguen existiendo para los demás.
    """
    cuerpo, nueva, actual_visto = leer_cuerpo(request)
    if cuerpo is None:
        return JsonResponse({'success': False, 'error': 'Datos inválidos.'}, status=400)

    proyecto, inicio, fin = datos_quincena(id_proyecto, anio, mes, quincena)
    empleado = get_object_or_404(Empleado, pk=cedula)

    with transaction.atomic():
        bloquear_quincena(proyecto, inicio, fin)
        actual, ultimo = limites_del_ingreso(proyecto, empleado, inicio, fin)
        if actual is None or actual != actual_visto:
            return JsonResponse({'success': False, 'error': ERROR_CAMBIO}, status=409)
        no_nuevo = error_si_no_es_nuevo(empleado, inicio, actual)
        if no_nuevo:
            return no_nuevo
        error = error_nueva_fecha(nueva, actual, ultimo, inicio)
        if error or nueva < actual:
            return JsonResponse({'success': False, 'error': error or 'La nueva fecha no es posterior a la actual.'}, status=400)

        a_borrar = registros_del_empleado(proyecto, empleado, actual, nueva - timedelta(days=1))
        eliminados = a_borrar.count()     # .delete() también cuenta las comidas y horas borradas en cascada
        # El borrado en cascada se lleva también sus comidas, salidas múltiples y horas históricas
        a_borrar.delete()

    return JsonResponse({'success': True, 'eliminados': eliminados})
