"""Liquidación quincenal de horas extra de un empleado.

Reglas (ver horas_extra.md, decisiones D1 a D11):
    - Días hábiles: lunes a viernes sin festivos. Jornada: 8,5 h de lunes a jueves y 8 h el viernes.
    - Horas efectivas = (salida - entrada) - comida - salidas temporales. Si la salida es menor que la
        entrada, el turno pasa a la medianoche (la salida es del día siguiente).
    - Las extras se identifican día a día: en un día hábil, lo que pasa de la jornada al final del turno;
        en sábado, domingo y festivo, todo el turno.
    - Cada tramo se clasifica por el día calendario en que se trabaja y por franja
        (diurna 6:00 a 19:00, nocturna 19:00 a 6:00): 4 tipos de extra.
    - La deuda (ausentismo, permiso no remunerado y horas que faltaron en días cortos) solo se paga con
        extras ordinarias diurnas (HEO). La sanción no se compensa con nada.
    - Las horas totales solo cuentan los días de asistencia. Incapacidad, vacaciones, licencia y permiso remunerado
        (GRUPO_B) no suman horas: dejan un hueco de jornada que cubren las extras ordinarias diurnas, después de la
        deuda. Lo que sobre de HEO se paga como extra; si no alcanzan, no se debe nada (lo paga la novedad).
    - Las horas históricas a favor se suman después de la nivelación; las de deducción solo generan aviso.

Todo se calcula en minutos enteros para no arrastrar errores de redondeo.
"""
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from .festivos import es_festivo

# ---------- Tipos de extra ----------
HEO = 'heo_diurna'
NOCTURNA = 'nocturna_ord'
DOM_DIURNA = 'dominical_diurna'
DOM_NOCTURNA = 'dominical_nocturna'
TIPOS = (HEO, NOCTURNA, DOM_DIURNA, DOM_NOCTURNA)
NOMBRES_TIPO = {
    HEO: 'Extra ordinaria diurna',
    NOCTURNA: 'Extra nocturna ordinaria',
    DOM_DIURNA: 'Extra dominical/festiva diurna',
    DOM_NOCTURNA: 'Extra dominical/festiva nocturna',
}

INICIO_DIURNO = 6 * 60       # 6:00 a.m.
INICIO_NOCTURNO = 19 * 60    # 7:00 p.m.

# ---------- Novedades ----------
ASISTENCIA = 'Asistencia'
GRUPO_A_CON_DEUDA = {'Ausentismo', 'Permiso no remunerado'}   # AU y PNR: la jornada se debe
SANCION = 'Sanción'                                            # descuento directo, no se compensa
GRUPO_B = {'Incapacidad general', 'Incapacidad laboral', 'Permiso remunerado', 'Vacaciones', 'Licencia'}
RETIRO = 'Retiro'
DESCANSO = 'Descanso'   # sábados, domingos y festivos sin trabajo: no suma horas, no genera deuda ni entra al resumen

# Jornada por día de la semana (0 = lunes) en minutos: 8,5 h de lunes a jueves y 8 h el viernes.
# Solo el desarrollador la cambia, aquí.
JORNADAS_POR_DEFECTO = {0: 510, 1: 510, 2: 510, 3: 510, 4: 480}

# Comida habitual: solo se descuenta lo que el turno cruza de estas franjas (nombre del proyecto en minúsculas).
# Se cambia aquí; los proyectos que no aparecen usan COMIDAS_POR_DEFECTO.
COMIDAS_POR_DEFECTO = [('almuerzo', time(12, 0), time(13, 0))]
COMIDAS_POR_PROYECTO = {
    'ciudadela andina': [('desayuno', time(8, 0), time(8, 30)), ('almuerzo', time(12, 0), time(13, 0))],
}

# Tipo de las horas históricas guardadas -> tipo de extra del informe
MAPA_HISTORICAS = {
    'Extras Diurnas': HEO,
    'Extras Nocturnas': NOCTURNA,
    'Festivas Diurnas': DOM_DIURNA,
    'Festivas Nocturnas': DOM_NOCTURNA,
}


@dataclass
class DiaEmpleado:
    """Lo guardado de un empleado en un día (un RegistroEntradaSalida)."""
    fecha: date
    novedad: str
    entrada: time = None
    salida: time = None
    comida_min: int = 0
    multiples: list = field(default_factory=list)      # [(hora de salida, hora de ingreso)] dentro del turno
    historicas: list = field(default_factory=list)     # [(accion, tipo de hora, minutos)]


# ---------- Calendario ----------
def es_habil(d):
    return d.weekday() < 5 and not es_festivo(d)


def jornada_min(d, jornadas):
    return jornadas.get(d.weekday(), 0) if es_habil(d) else 0


def dias_habiles(inicio, fin):
    d = inicio
    while d <= fin:
        if es_habil(d):
            yield d
        d += timedelta(days=1)


def ultimo_dia_habil_antes(fecha, desde):
    """Último día hábil anterior a `fecha` que no sea anterior a `desde`; None si no hay ninguno."""
    dia = fecha - timedelta(days=1)
    while dia >= desde:
        if es_habil(dia):
            return dia
        dia -= timedelta(days=1)
    return None


# ---------- Tiempo ----------
def _minutos(delta):
    return int(delta.total_seconds() // 60)


def turno(dia):
    """(inicio, fin) del turno principal; si la salida es menor que la entrada, termina al día siguiente."""
    ini = datetime.combine(dia.fecha, dia.entrada)
    fin = datetime.combine(dia.fecha, dia.salida)
    if fin < ini:
        fin += timedelta(days=1)
    return ini, fin


def _ubicar(hora, ini):
    """Pone una hora suelta dentro del turno que empieza en `ini`."""
    dt = datetime.combine(ini.date(), hora)
    return dt + timedelta(days=1) if dt < ini else dt


def _tramos_multiples(dia, ini):
    tramos = []
    for salida, ingreso in dia.multiples:
        a, b = _ubicar(salida, ini), _ubicar(ingreso, ini)
        if b > a:
            tramos.append((a, b))
    return tramos


def minutos_efectivos(dia):
    """(salida - entrada) - comida - salidas temporales, en minutos."""
    if not dia.entrada or not dia.salida:
        return 0
    ini, fin = turno(dia)
    ausencias = sum(_minutos(b - a) for a, b in _tramos_multiples(dia, ini))
    return max(0, _minutos(fin - ini) - dia.comida_min - ausencias)


def comidas_habituales_del_turno(nombre_proyecto, fecha, entrada, salida):
    """[(tipo, inicio, fin)]: lo que el turno cruza de las franjas de comida habituales del proyecto.

    Un turno que sale a las 12:00 no cruza el almuerzo; uno que sale a las 12:30 cruza media hora (12:00 a 12:30).
    Un turno que pasa la medianoche revisa también el día siguiente.
    """
    if not entrada or not salida:
        return []
    ini, fin = datetime.combine(fecha, entrada), datetime.combine(fecha, salida)
    if fin < ini:
        fin += timedelta(days=1)
    franjas = COMIDAS_POR_PROYECTO.get((nombre_proyecto or '').strip().lower(), COMIDAS_POR_DEFECTO)
    cruces = []
    for dia in (fecha, fecha + timedelta(days=1)):
        for tipo, desde, hasta in franjas:
            a, b = max(ini, datetime.combine(dia, desde)), min(fin, datetime.combine(dia, hasta))
            if b > a:
                cruces.append((tipo, a.time(), b.time()))
    return cruces


def comida_habitual_min(nombre_proyecto, fecha, entrada, salida):
    """Minutos de comida habitual que se restan: la suma de lo que el turno cruza de las franjas del proyecto."""
    return sum(
        (b.hour * 60 + b.minute) - (a.hour * 60 + a.minute)
        for _, a, b in comidas_habituales_del_turno(nombre_proyecto, fecha, entrada, salida)
    )


# ---------- Clasificación por día y franja ----------
def partir_en_medianoche(ini, fin):
    """Parte un intervalo en tramos que no cruzan la medianoche: cada tramo se clasifica con su día calendario."""
    tramos, actual = [], ini
    while actual < fin:
        corte = min(fin, datetime.combine(actual.date() + timedelta(days=1), time.min))
        tramos.append((actual, corte))
        actual = corte
    return tramos


def clasificar_intervalo(ini, fin):
    """Minutos de [ini, fin) por tipo de extra."""
    res = Counter()
    for a, b in partir_en_medianoche(ini, fin):
        dominical = a.weekday() == 6 or es_festivo(a.date())
        desde = a.hour * 60 + a.minute
        hasta = desde + _minutos(b - a)
        diurnos = max(0, min(hasta, INICIO_NOCTURNO) - max(desde, INICIO_DIURNO))
        diurno, nocturno = (DOM_DIURNA, DOM_NOCTURNA) if dominical else (HEO, NOCTURNA)
        res[diurno] += diurnos
        res[nocturno] += (hasta - desde) - diurnos
    return res


def _restar(contador, claves, minutos):
    """Quita `minutos` de las claves indicadas, en ese orden de preferencia."""
    for clave in claves:
        quitar = min(contador[clave], minutos)
        contador[clave] -= quitar
        minutos -= quitar
        if minutos <= 0:
            break


def extras_del_dia(dia, jornadas):
    """(extras por tipo en minutos, minutos efectivos, minutos que faltaron para la jornada)."""
    efectivos = minutos_efectivos(dia)
    jornada = jornada_min(dia.fecha, jornadas)
    if not dia.entrada or not dia.salida:
        return Counter(), 0, jornada
    ini, fin = turno(dia)

    if es_habil(dia.fecha):
        sobrante = efectivos - jornada
        if sobrante <= 0:
            return Counter(), efectivos, -sobrante
        # Las extras son lo que pasa de la jornada, al final del turno (D8)
        return clasificar_intervalo(fin - timedelta(minutes=sobrante), fin), efectivos, 0

    # Sábado, domingo o festivo: todo el turno es extra, menos la comida y las salidas temporales
    extras = clasificar_intervalo(ini, fin)
    for a, b in _tramos_multiples(dia, ini):
        for tipo, minutos in clasificar_intervalo(a, b).items():
            extras[tipo] -= minutos
    # La comida se descuenta de la franja diurna del día en que empieza el turno
    dominical = dia.fecha.weekday() == 6 or es_festivo(dia.fecha)
    diurno, nocturno = (DOM_DIURNA, DOM_NOCTURNA) if dominical else (HEO, NOCTURNA)
    _restar(extras, (diurno, nocturno), dia.comida_min)
    return extras, efectivos, 0


# ---------- Liquidación de un empleado ----------
def horas_de(minutos):
    """Minutos -> horas con 2 decimales."""
    return (Decimal(minutos) / 60).quantize(Decimal('0.01'))


def liquidar(dias, fin_quincena, jornadas=None, inicio_quincena=None):
    """Resultado de la quincena de un empleado a partir de sus días registrados.

    Con `inicio_quincena` detecta al empleado nuevo: si su primer registro no es el inicio de la quincena (quedan días
    hábiles antes), `fecha_ingreso` trae esa fecha y su umbral cuenta solo los días hábiles desde ahí hasta el final.
    """
    jornadas = jornadas or JORNADAS_POR_DEFECTO
    extras = Counter()
    deuda_ausencias = faltantes = total = umbral = huecos = 0
    resumen, sanciones, deducciones = Counter(), [], Counter()
    pendientes = Counter()
    retiro = None

    for dia in sorted(dias, key=lambda d: d.fecha):
        jornada = jornada_min(dia.fecha, jornadas)
        if dia.novedad not in (ASISTENCIA, DESCANSO):
            resumen[dia.novedad] += 1

        if dia.novedad == ASISTENCIA:
            ex, efectivos, falta = extras_del_dia(dia, jornadas)
            extras.update(ex)
            total += efectivos
            faltantes += falta
            umbral += jornada
        elif dia.novedad in GRUPO_B:
            huecos += jornada      # no suma a las horas totales: las HEO pueden cubrir este hueco, sin generar deuda
            umbral += jornada
        elif dia.novedad in GRUPO_A_CON_DEUDA:
            deuda_ausencias += jornada
        elif dia.novedad == SANCION:
            sanciones.append(dia.fecha)
        elif dia.novedad == RETIRO:
            retiro = dia.fecha

        for accion, tipo, minutos in dia.historicas:
            (pendientes if accion == 'Pendiente' else deducciones)[tipo] += minutos

    # Control de cuadre: lo que supera el umbral quincenal debe ser igual a las extras menos lo que faltó y los huecos
    cuadra = (total - umbral) == (sum(extras.values()) - faltantes - huecos)

    # Nivelación: solo las HEO pagan la deuda; nocturnas, dominicales y festivas nunca
    deuda = deuda_ausencias + faltantes
    pago = min(extras[HEO], deuda)
    extras[HEO] -= pago
    deuda -= pago

    # Lo que sobre de HEO cubre el hueco de incapacidades, vacaciones, licencias y permisos remunerados; si no
    # alcanza, el resto no se debe (lo paga la novedad)
    extras[HEO] -= min(extras[HEO], huecos)

    # Saldo histórico a favor: se suma al final, sin entrar a la nivelación
    for tipo, minutos in pendientes.items():
        extras[MAPA_HISTORICAS.get(tipo, HEO)] += minutos

    novedades = [f"{fecha:%d/%m/%Y}: sanción, día no pagado" for fecha in sanciones]
    for tipo, minutos in sorted(deducciones.items()):
        novedades.append(
            f"Al empleado se le deberá deducir {horas_de(minutos).normalize():f} horas del tipo: "
            f"{NOMBRES_TIPO[MAPA_HISTORICAS.get(tipo, HEO)].lower()}"
        )

    # Empleado nuevo (umbral dinámico): el umbral de arriba ya cuenta solo los días con registro, es decir, desde su ingreso
    primer_registro = min((d.fecha for d in dias), default=None)
    fecha_ingreso = dias_desde_ingreso = None
    if inicio_quincena and primer_registro and any(True for _ in dias_habiles(inicio_quincena, primer_registro - timedelta(days=1))):
        fecha_ingreso = primer_registro
        dias_desde_ingreso = sum(1 for _ in dias_habiles(primer_registro, fin_quincena))

    # Días de retiro: todos los días del calendario (hábiles o no) desde el día siguiente al último día hábil anterior al retiro
    # hasta el final de la quincena. Si trabajó hasta el viernes y el retiro se marcó el lunes, el sábado y el domingo ya son
    # del retiro (ni descanso ni jornada), y el lunes también.
    dias_retiro = 0
    if retiro:
        ultimo_habil = ultimo_dia_habil_antes(retiro, retiro - timedelta(days=14))
        arranque = ultimo_habil + timedelta(days=1) if ultimo_habil else retiro
        if inicio_quincena:
            arranque = max(arranque, inicio_quincena)
        dias_retiro = max((fin_quincena - arranque).days + 1, 0)

    # Horas base de la quincena: la jornada de todos los días hábiles que le corresponden a la persona, desde su ingreso
    # (o el inicio de la quincena) hasta el final o hasta el día ANTERIOR a su retiro. No descuenta ausencias ni permisos:
    # es lo que se esperaba de ella en el periodo (el umbral de arriba, en cambio, solo cuenta los días en que sí tuvo jornada).
    # El día del retiro no cuenta: ese día su novedad es «Retiro», no trabaja y no se le descuenta nada.
    desde_base = fecha_ingreso or inicio_quincena or primer_registro
    hasta_base = retiro - timedelta(days=1) if retiro else fin_quincena
    base = sum(jornada_min(d, jornadas) for d in dias_habiles(desde_base, hasta_base)) if primer_registro else 0

    return {
        'extras': {tipo: horas_de(extras[tipo]) for tipo in TIPOS},
        'horas_deducir': horas_de(deuda),
        'resumen_novedades': dict(resumen),
        'novedades_deducir': novedades,
        'dias_retiro': dias_retiro,
        'fecha_retiro': retiro,
        'fecha_ingreso': fecha_ingreso,
        'dias_desde_ingreso': dias_desde_ingreso,
        'cuadra': cuadra,
        'total': horas_de(total),
        'umbral': horas_de(umbral),
        'horas_base': horas_de(base),
    }
