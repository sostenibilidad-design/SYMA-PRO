from django.db.models import Avg,  IntegerField, Count, Max
from django.db.models.functions import ExtractMonth, Cast, TruncDate, TruncMonth
from datetime import timedelta
from django.utils.formats import date_format
from django.http import JsonResponse
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR
from collections import Counter

from medicion_rendimiento.models import MedicionCuadrilla

MIN_DATOS_DIAGNOSTICO = 30
ANCHO_CLUSTER = Decimal("2")

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

def demanda_empleados_por_actividad(proyecto, fecha_inicio, fecha_fin, modo="mes"):
    # 1. FILTRO BASE: Combinaciones únicas de Persona+Actividad+Fecha
    # Esto evita que si Juan marcó 2 veces el MISMO día en la misma actividad, se cuente doble ese día.
    registros_unicos = (
        MedicionCuadrilla.objects
        .filter(proyecto=proyecto, fecha__range=(fecha_inicio, fecha_fin))
        .values("empleados", "actividad", "fecha")
        .distinct()
    )

    if not registros_unicos.exists():
        return {"labels": [], "datasets": []}

    # 2. CONTEO DIARIO: ¿Cuántas cabezas hubo cada día?
    conteo_diario = {} # {(actividad, fecha): cantidad_personas}

    for reg in registros_unicos:
        key = (reg["actividad"], reg["fecha"])
        conteo_diario[key] = conteo_diario.get(key, 0) + 1

    # ---------------------------------------------------------
    # MODO DÍA: Muestra la cantidad exacta de cada día
    # ---------------------------------------------------------
    if modo == "dia":
        total_dias = (fecha_fin - fecha_inicio).days + 1
        fechas = [fecha_inicio + timedelta(days=i) for i in range(total_dias)]
        labels = [date_format(f, "d M") for f in fechas]
        
        actividades = sorted(list(set(k[0] for k in conteo_diario.keys())))
        datasets = []
        
        for act in actividades:
            datasets.append({
                "label": act,
                "data": [conteo_diario.get((act, f), 0) for f in fechas]
            })
        return {"labels": labels, "datasets": datasets}

    # ---------------------------------------------------------
    # MODO MES: SUMA ACUMULADA (La corrección que pediste)
    # ---------------------------------------------------------
    else:
        datos_mensuales = {} # {(actividad, primer_dia_mes): suma_total}
        meses_set = set()

        for (act, fecha), cantidad_dia in conteo_diario.items():
            # Agrupamos por el primer día del mes
            mes_key = fecha.replace(day=1)
            meses_set.add(mes_key)
            
            key_mes = (act, mes_key)
            
            # 🔥 AQUÍ ESTÁ EL CAMBIO: SUMAMOS (+) EN LUGAR DE REEMPLAZAR
            # Día 20 (8 personas) + Día 22 (4 personas) = 12 en el Mes
            datos_mensuales[key_mes] = datos_mensuales.get(key_mes, 0) + cantidad_dia

        # Ordenar etiquetas
        meses_ordenados = sorted(list(meses_set))
        labels = [date_format(m, "M Y") for m in meses_ordenados]
        
        # Crear datasets
        actividades = sorted(list(set(k[0] for k in datos_mensuales.keys())))
        datasets = []
        
        for act in actividades:
            datasets.append({
                "label": act,
                "data": [datos_mensuales.get((act, m), 0) for m in meses_ordenados]
            })

        return {"labels": labels, "datasets": datasets}

def diagnostico_rendimiento_real(mediciones_qs):

    valores = list(
        mediciones_qs
        .filter(rendimiento_real__isnull=False)
        .values_list("rendimiento_real", flat=True)
    )

    if len(valores) < MIN_DATOS_DIAGNOSTICO:
        return {
            "promedio": 0,
            "estado": "SIN DATOS",
            "valores": [],
            "rangos": None,
            "habilitado": False
        }

    valores_d = [Decimal(v).quantize(Decimal("0.01")) for v in valores]

    # 🔹 PROMEDIO → SOLO PARA LA AGUJA
    promedio = (
        sum(valores_d) / Decimal(len(valores_d))
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 🔹 CLUSTERIZACIÓN (bins visuales)
    clusters = [
        (v / ANCHO_CLUSTER).to_integral_value(rounding=ROUND_FLOOR) * ANCHO_CLUSTER
        for v in valores_d
    ]

    conteo = Counter(clusters)

    MIN_REPETICIONES_CLUSTE = max(3, int(len(valores_d) * 0.08))

    # 🔹 ACEPTABLE → cluster más repetido y estable
    aceptable, freq = conteo.most_common(1)[0]

    # 🔹 CRÍTICO → cluster inferior con suficientes datos
    criticos = [
        c for c, f in conteo.items()
        if c < aceptable and f >= MIN_REPETICIONES_CLUSTE
    ]
    critico = max(criticos) if criticos else aceptable - ANCHO_CLUSTER

    # 🔹 EXCELENTE → cluster superior con suficientes datos
    excelentes = [
        c for c, f in conteo.items()
        if c > aceptable and f >= MIN_REPETICIONES_CLUSTE
    ]
    excelente = min(excelentes) if excelentes else aceptable + ANCHO_CLUSTER

    # 🔹 ESTADO (solo texto)
    if promedio < critico:
        estado = "CRITICO"
    elif promedio < excelente:
        estado = "ACEPTABLE"
    else:
        estado = "EXCELENTE"

    return {
        "promedio": float(promedio),
        "estado": estado,
        "valores": [float(v) for v in valores_d],
        "rangos": {
            "critico": float(critico),
            "aceptable": float(aceptable),
            "excelente": float(excelente),
        },
        "habilitado": True,
        "cantidad_datos": len(valores_d)
    }

def diagnostico_costo_por_unidad(registros, presupuesto_unitario):
    costos = []

    for r in registros:
        if r.costo_por_unidad is not None and r.costo_por_unidad > 0:
            costos.append(float(r.costo_por_unidad))

    cantidad_datos = len(costos)

    if cantidad_datos == 0:
        return {
            "promedio": 0,
            "estado": "SIN DATOS",
            "cantidad_datos": 0,
            "rangos": {
                "critico": 0,
                "aceptable": 0,
                "excelente": 0
            }
        }

    promedio = sum(costos) / cantidad_datos

    excelente = float(presupuesto_unitario)
    aceptable = excelente * 1.10
    critico   = excelente * 1.25

    if promedio <= excelente:
        estado = "EXCELENTE"
    elif promedio <= aceptable:
        estado = "ACEPTABLE"
    else:
        estado = "CRÍTICO"

    return {
        "promedio": round(promedio, 2),
        "estado": estado,
        "cantidad_datos": cantidad_datos,
        "rangos": {
            "critico": round(critico, 2),
            "aceptable": round(aceptable, 2),
            "excelente": round(excelente, 2)
        }
    }

def comparativo_rendimiento_cuadrillas(proyecto, actividad, fecha_inicio, fecha_fin):
    """
    Comparativo de Rendimiento Real (u/h).
    - Thresholds (Líneas): Calculados con todo el histórico de la actividad (Estabilidad).
    - Barras: Calculadas solo con el rango de fechas seleccionado.
    - REGLA DE ORO: Se requieren mínimo 30 datos históricos para calcular thresholds.
    """

    MIN_DATOS_REQUERIDOS = 30
    
    # 1. QUERY GLOBAL (HISTÓRICO) 
    qs_historico = MedicionCuadrilla.objects.filter(
        proyecto=proyecto,
        actividad=actividad,
        rendimiento_real__gt=0  
    ).values_list('rendimiento_real', flat=True)

    valores_globales = [float(v) for v in qs_historico]
    cantidad_datos = len(valores_globales)
    
    if cantidad_datos < MIN_DATOS_REQUERIDOS:
        return {
            "labels": [],
            "data": [],
            "thresholds": {
                "bajo": 0,
                "estandar": 0,
                "superior": 0
            },
            "integrantes": [],
            "estado": "INSUFICIENTE" 
        }

    bajo = 0
    estandar = 0
    superior = 0
    
    promedio_simple = sum(valores_globales) / cantidad_datos
    step = max(0.5, promedio_simple * 0.05) 
    clusters = [round(v / step) * step for v in valores_globales]
    conteo = Counter(clusters)
    
    if conteo:
        modo_estandar = conteo.most_common(1)[0][0]
        estandar = modo_estandar
        
        candidatos_sup = [k for k, v in conteo.items() if k > estandar * 1.1 and v > 2]
        if candidatos_sup:
            superior = min(candidatos_sup) 
        else:
            superior = estandar * 1.25 

        candidatos_inf = [k for k, v in conteo.items() if k < estandar * 0.85 and v > 2]
        if candidatos_inf:
            bajo = max(candidatos_inf) 
        else:
            bajo = estandar * 0.75 

    qs_periodo = MedicionCuadrilla.objects.filter(
        proyecto=proyecto,
        actividad=actividad,
        fecha__range=(fecha_inicio, fecha_fin),
        rendimiento_real__gt=0
    )

    datos_cuadrillas = (
        qs_periodo
        .values('cuadrilla')
        .annotate(promedio=Avg('rendimiento_real'))
        .order_by('cuadrilla')
    )

    labels = []
    data = []
    metadata_integrantes = []

    for item in datos_cuadrillas:
        num_cuadrilla = item['cuadrilla']
        promedio = round(float(item['promedio']), 2)
        
        labels.append(f"Cuadrilla {num_cuadrilla}")
        data.append(promedio)

        integrantes_qs = (
            qs_periodo
            .filter(cuadrilla=num_cuadrilla)
            .values_list('nombre_empleado', flat=True)
        )
        
        nombres_set = set()
        for raw in integrantes_qs:
            if raw:
                partes = raw.replace('<br>', ',').split(',')
                for p in partes:
                    nombre_limpio = p.strip().title()
                    if nombre_limpio: 
                        nombres_set.add(nombre_limpio)
        
        metadata_integrantes.append(sorted(list(nombres_set)))

    return {
        "labels": labels,
        "data": data,
        "thresholds": {
            "bajo": round(bajo, 2),
            "estandar": round(estandar, 2),
            "superior": round(superior, 2)
        },
        "integrantes": metadata_integrantes,
        "estado": "OK"
    }

def cronograma_actividades(proyecto, fecha_inicio, fecha_fin):
    """
    Estructura Jerárquica para Motor Canvas (Jira Style).
    Retorna lista de objetos con 'hijos' para poder desplegar.
    """
    mediciones = MedicionCuadrilla.objects.filter(
        proyecto=proyecto,
        fecha__range=(fecha_inicio, fecha_fin)
    ).order_by('actividad', 'ubicacion', 'fecha')

    if not mediciones.exists():
        return []

    agrupacion = {}

    for m in mediciones:
        act = m.actividad
        fecha = m.fecha
        raw_loc = m.ubicacion or "General"
        # Normalizar ubicación para agrupar (ej: "torre 1" == "Torre 1")
        loc_key = " ".join(sorted(raw_loc.lower().split())) 
        loc_display = raw_loc.capitalize()

        if act not in agrupacion:
            agrupacion[act] = {
                'inicio_global': fecha,
                'fin_global': fecha,
                'hijos_map': {}
            }
        
        parent = agrupacion[act]
        # Extender fechas del padre
        if fecha < parent['inicio_global']: parent['inicio_global'] = fecha
        if fecha > parent['fin_global']: parent['fin_global'] = fecha

        if loc_key not in parent['hijos_map']:
            parent['hijos_map'][loc_key] = {
                'nombre': loc_display,
                'inicio': fecha,
                'fin': fecha
            }
        
        child = parent['hijos_map'][loc_key]
        if fecha < child['inicio']: child['inicio'] = fecha
        if fecha > child['fin']: child['fin'] = fecha

    # Generar lista plana para JSON
    resultado = []
    colores = ['#0052CC', '#36B37E', '#FFAB00', '#FF5630', '#6554C0', '#00B8D9'] # Colores Jira
    
    for i, (nombre_act, datos) in enumerate(sorted(agrupacion.items())):
        lista_hijos = []
        for _, h in datos['hijos_map'].items():
            lista_hijos.append({
                'nombre': h['nombre'],
                'inicio': h['inicio'].strftime("%Y-%m-%d"),
                'fin': h['fin'].strftime("%Y-%m-%d")
            })
        
        # Ordenar hijos por fecha
        lista_hijos.sort(key=lambda x: x['inicio'])

        resultado.append({
            'id': i + 1,
            'nombre': nombre_act,
            'inicio': datos['inicio_global'].strftime("%Y-%m-%d"),
            'fin': datos['fin_global'].strftime("%Y-%m-%d"),
            'color': colores[i % len(colores)],
            'hijos': lista_hijos, # <--- ESTO ES LA CLAVE DEL DESPLIEGUE
            'expandido': False
        })

    return resultado