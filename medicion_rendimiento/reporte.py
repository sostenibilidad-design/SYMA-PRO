import calendar
import re

from django.db.models import Avg,  IntegerField, Count, Max
from django.db.models.functions import ExtractMonth, Cast, TruncDate, TruncMonth
from datetime import timedelta
from django.utils.formats import date_format
from django.http import JsonResponse
from decimal import Decimal, ROUND_HALF_UP

from medicion_rendimiento.models import MedicionCuadrilla

def MESES_ES ():
    return [
        "ene", "feb", "mar", "abr", "may", "jun",
        "jul", "ago", "sep", "oct", "nov", "dic"
    ]

def rendimiento_real_mensual(proyecto, actividad):
    # Validación defensiva
    if not proyecto or not actividad:
        return [], []

    # Query base
    qs = (
        MedicionCuadrilla.objects
        .filter(
            proyecto=proyecto,
            actividad=actividad,
            rendimiento_real__isnull=False
        )
        .annotate(mes=ExtractMonth('fecha'))
        .values('mes')
        .annotate(promedio=Avg('rendimiento_real'))
        .order_by('mes')
    )

    # Inicializar los 12 meses (registros irregulares)
    rendimiento_por_mes = {i: 0 for i in range(1, 13)}

    for fila in qs:
        rendimiento_por_mes[fila['mes']] = round(float(fila['promedio']), 2)

    # Labels y data finales
    labels = MESES_ES ()
    data = [rendimiento_por_mes[i] for i in range(1, 13)]

    return labels, data

def rendimiento_real_diario_por_cuadrilla(
    proyecto,
    actividad,
    fecha_inicio,
    fecha_fin
):

    # Rango completo de fechas
    total_dias = (fecha_fin - fecha_inicio).days + 1
    fechas = [
        fecha_inicio + timedelta(days=i)
        for i in range(total_dias)
    ]

    labels = [date_format(f, "d M") for f in fechas]

    # Query base
    qs = (
        MedicionCuadrilla.objects
        .filter(
            proyecto=proyecto,
            actividad=actividad,
            fecha__range=(fecha_inicio, fecha_fin)
        )
        .annotate(cuadrilla_norm=Cast("cuadrilla", IntegerField()))
        .values("cuadrilla_norm", "fecha")
        .annotate(promedio=Avg("rendimiento_real"))
        .order_by("cuadrilla_norm", "fecha")
    )

    # Agrupar por cuadrilla
    data_por_cuadrilla = {}

    for fila in qs:
        cuadrilla = fila["cuadrilla_norm"]
        fecha = fila["fecha"]
        valor = fila["promedio"]

        if cuadrilla not in data_por_cuadrilla:
            data_por_cuadrilla[cuadrilla] = {}

        data_por_cuadrilla[cuadrilla][fecha] = (round(float(valor), 2) if valor is not None else None)

    # CASO SIN DATOS
    if not data_por_cuadrilla:
        return [{
            "cuadrilla": 0,
            "labels": labels,
            "rendimiento_real": [None] * len(labels)
        }]
    
    resultado = []

    for cuadrilla, mapa in data_por_cuadrilla.items():
        valores = [
            mapa.get(fecha, None)
            for fecha in fechas
        ]

        resultado.append({
            "cuadrilla": cuadrilla,
            "labels": labels,
            "rendimiento_real": valores
        })

    return resultado

def costo_por_unidad_diario_por_cuadrilla(
    proyecto,
    actividad,
    fecha_inicio,
    fecha_fin
):

    # Rango completo de fechas
    total_dias = (fecha_fin - fecha_inicio).days + 1
    fechas = [
        fecha_inicio + timedelta(days=i)
        for i in range(total_dias)
    ]

    labels = [date_format(f, "d M") for f in fechas]

    # Query base
    qs = (
        MedicionCuadrilla.objects
        .filter(
            proyecto=proyecto,
            actividad=actividad,
            fecha__range=(fecha_inicio, fecha_fin),
        )
        .annotate(cuadrilla_norm=Cast("cuadrilla", IntegerField()))
        .values("cuadrilla_norm", "fecha")
        .annotate(promedio=Avg("costo_por_unidad"))
        .order_by("cuadrilla_norm", "fecha")
    )

    data_por_cuadrilla = {}

    for fila in qs:
        cuadrilla = fila["cuadrilla_norm"]
        fecha = fila["fecha"]
        valor = fila["promedio"]

        if cuadrilla not in data_por_cuadrilla:
            data_por_cuadrilla[cuadrilla] = {}

        data_por_cuadrilla[cuadrilla][fecha] = (round(float(valor), 2) if valor is not None else None)

    # CASO SIN DATOS
    if not data_por_cuadrilla:
        return [{
            "cuadrilla": 0,
            "labels": labels,
            "costo_por_unidad": [None] * len(labels)
        }]

    resultado = []

    for cuadrilla, mapa in data_por_cuadrilla.items():
        valores = [
            mapa.get(fecha, None)
            for fecha in fechas
        ]

        resultado.append({
            "cuadrilla": cuadrilla,
            "labels": labels,
            "costo_por_unidad": valores
        })

    return resultado


def demanda_empleados_por_actividad(
    proyecto,
    fecha_inicio,
    fecha_fin,
    modo="mes"  
):

    # Personas únicas por día
    qs_base = (
        MedicionCuadrilla.objects
        .filter(
            proyecto=proyecto,
            fecha__range=(fecha_inicio, fecha_fin)
        )
        .values("actividad", "fecha")
        .annotate(
            personas=Count("empleados", distinct=True)
        )
    )

    if not qs_base.exists():
        return {"labels": [], "datasets": []}

    # MODO DÍA
    if modo == "dia":
        total_dias = (fecha_fin - fecha_inicio).days + 1
        fechas = [
            fecha_inicio + timedelta(days=i)
            for i in range(total_dias)
        ]
        labels = [date_format(f, "d M") for f in fechas]

        data = {}

        for q in qs_base:
            act = q["actividad"]
            fecha = q["fecha"]

            data.setdefault(act, {})
            data[act][fecha] = q["personas"]

        datasets = [
            {
                "label": act,
                "data": [valores.get(f, 0) for f in fechas]
            }
            for act, valores in data.items()
        ]

        return {"labels": labels, "datasets": datasets}

    # MODO MES
    qs_mes = (
        qs_base
        .annotate(mes=TruncMonth("fecha"))
        .values("actividad", "mes")
        .annotate(
            total=Count("fecha")
        )
        .order_by("mes")
    )

    meses = sorted({q["mes"] for q in qs_mes})
    labels = [date_format(m, "M Y") for m in meses]

    data = {}

    for q in qs_mes:
        act = q["actividad"]
        mes = q["mes"]

        data.setdefault(act, {})
        data[act][mes] = q["total"]

    datasets = [
        {
            "label": act,
            "data": [valores.get(m, 0) for m in meses]
        }
        for act, valores in data.items()
    ]

    return {"labels": labels, "datasets": datasets}

def diagnostico_rendimiento_real(mediciones_qs):

    valores = list(
        mediciones_qs
        .filter(rendimiento_real__isnull=False)
        .values_list("rendimiento_real", flat=True)
    )

    if not valores:
        return {
            "promedio": 0,
            "min": 0,
            "max": 0,
            "valores": []
        }

    valores_decimal = [Decimal(v) for v in valores]

    promedio = (
        sum(valores_decimal) / Decimal(len(valores_decimal))
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "promedio": float(promedio),
        "min": float(min(valores_decimal)),
        "max": float(max(valores_decimal)),
        "valores": [float(v) for v in valores_decimal]
    }
