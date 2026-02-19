import json
import re
import calendar
from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from datetime import datetime, date, timedelta, time
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce,  ExtractMonth

from .forms import MedicionInicioForm, MedicionFinForm, CumplimientoForm, HistorialCambiosCuadrillaForm, ConfiguracionAlertaForm
from .models import MedicionCuadrilla, Cumplimiento, HistorialCambiosCuadrilla, ConsumoAlimento, ConfiguracionAlerta
from personal.models import Empleado, ValorHora 
from usuario.models import Usuario
from medicion_rendimiento.reporte import (
    rendimiento_real_mensual, rendimiento_real_diario_por_cuadrilla, 
    costo_por_unidad_diario_por_cuadrilla, demanda_empleados_por_actividad,
    diagnostico_rendimiento_real, diagnostico_costo_por_unidad,
    comparativo_rendimiento_cuadrillas, cronograma_actividades,
    )

def formato_colombia(valor):
    return "$ {:,.0f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

def es_contratista(emp):
    return "contratista" in (emp.cargo or "").lower()

# --- Medición de rendimiento por cuadrilla ---

def obtener_valor_hora_por_cargo(emp, valores):
    cargo = (emp.cargo or "").lower()

    if "ayudante" in cargo and "entendido" in cargo:
        return valores.ayudante_entendido

    if "ayudante" in cargo:
        return valores.ayudante_raso

    if "oficial junior" in cargo:
        return valores.oficial_junior

    if "oficial senior" in cargo:
        return valores.oficial_senior

    return Decimal("0.00") 

#  --- FUNCIÓN AUXILIAR DE FILTRO GENERAL ---
def filtrar_mediciones(request, queryset):
    filtros = Q()
    data = request.GET or request.POST

    fecha_inicio = data.get('fecha_inicio', '').strip()
    fecha_fin = data.get('fecha_fin', '').strip()
    actividad = data.get('actividad', '').strip()
    ubicacion = data.get('ubicacion', '').strip()
    cuadrilla = data.get('Cuadrilla', '').strip()
    cedula = data.get('cedula', '').strip()
    nombre = data.get('nombre', '').strip()
    rendimiento_real = data.get('rendimiento_real', '').strip()

    if fecha_inicio and fecha_fin:
        try:
            f_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            f_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

            filtros &= Q(fecha__gte=f_inicio, fecha__lte=f_fin)
        except ValueError:
            pass
    elif fecha_inicio: 
        try:
            f_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            filtros &= Q(fecha=f_inicio)
        except ValueError:
            pass
    elif fecha_fin: 
        try:
            f_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
            filtros &= Q(fecha__lte=f_fin)
        except ValueError:
            pass

    if actividad:
        filtros &= Q(actividad__icontains=actividad)

    if ubicacion:
        filtros &= Q(ubicacion__icontains=ubicacion)

    if cuadrilla:
        filtros &= Q(cuadrilla__icontains=cuadrilla)

    if cedula:
        filtros &= Q(empleado_cedula__icontains=cedula)

    if nombre:
        filtros &= Q(nombre_empleado__icontains=nombre)

    if rendimiento_real:
        try:
            valor = float(rendimiento_real)
            filtros &= Q(rendimiento_real__gte=valor)
        except ValueError:
            pass

    return queryset.filter(filtros)

def obtener_cumplimiento(request):
    """Retorna los datos de cumplimiento para una actividad dada."""
    actividad = request.GET.get('actividad')
    if not actividad:
        return JsonResponse({'error': 'Actividad no especificada'}, status=400)

    cumplimiento = Cumplimiento.objects.filter(actividad__iexact=actividad).first()
    if cumplimiento:
        data = {
            'unidad_medida': cumplimiento.unidad_medida,
            'cumplimiento_presupuestal': float(cumplimiento.cumplimiento_presupuestal or 0),
            'cumplimiento_programado': float(cumplimiento.cumplimiento_programado or 0),
        }
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'No se encontró cumplimiento para esta actividad'}, status=404)


def medicion_por_cuadrilla(request):
    # --- PRIMERO manejar borrado ---
    if request.method == "POST":
        seleccion = request.POST.get("elemento")
        accion = request.POST.get("accion")
        ids = [int(x) for x in seleccion.split(",") if x.strip().isdigit()] if seleccion else []

        if accion == "actualizar" and ids:
            pk = ids[0]
            return redirect("actualizar_cuadrilla", id=pk)

        if accion == "borrar" and ids:
            MedicionCuadrilla.objects.filter(pk__in=ids).delete()
            messages.success(request, "Rendimiento(s) eliminado(s) correctamente.")
            return redirect("actividad_cuadrilla")  # 🔥 evitar POST doble y refrescos erróneos

    # --- LUEGO cargar mediciones ---
    mediciones = MedicionCuadrilla.objects.all().order_by('-fecha', '-hora_inicio')
    mediciones = filtrar_mediciones(request, mediciones)

    cumplimientos_dict = {
        c.actividad.lower(): c.unidad_medida for c in Cumplimiento.objects.all()
    }

    for m in mediciones:
        m.unidad_medida = cumplimientos_dict.get(m.actividad.lower(), '')

    filas_vacias = max(0, 20 - mediciones.count())

    empleados = Empleado.objects.filter(
        Q(cargo__icontains='oficial') |
        Q(cargo__icontains='ayudante') |
        Q(cargo__icontains='contratista')
    ).order_by('nombre_completo')

    usuarios = Usuario.objects.all().order_by('nombre_completo')

    form = MedicionInicioForm()

    ultimo = Cumplimiento.objects.last()
    cumplimientos = Cumplimiento.objects.all().order_by('actividad')

    context = {
        "Cuadrillas": mediciones,
        "filas_vacias": range(filas_vacias),
        "empleados": empleados,
        "usuarios": usuarios,
        "form": form,
        "ultimo": ultimo,
        "Cumplimientos": cumplimientos,
        "alertas_configuradas": ConfiguracionAlerta.objects.all(),
    }
    return render(request, 'medicion_rendimiento/medicion_por_cuadrilla.html', context)

def registrar_inicio_medicion(request): 
    if request.method == 'POST':
        form = MedicionInicioForm(request.POST, request.FILES)
        if form.is_valid():
            medicion = form.save(commit=False)

            if request.user.is_authenticated:
                # CORRECCIÓN: Asignamos el usuario directamente
                medicion.usuario = request.user 
                
                # Opcional: Si tu modelo Usuario tiene campo 'cedula' y 'nombre_completo'
                medicion.usuario_cedula = getattr(request.user, 'cedula', None)
                medicion.nombre_usuario = getattr(request.user, 'nombre_completo', str(request.user))
            
            medicion.hora_inicio = timezone.localtime(timezone.now()).time()
            
            medicion.save()  # Guarda la medición principal
            form.save_m2m()  # Guarda la relación ManyToMany (empleados)

            # Conteo dentro de la cuadrilla: contamos entre los empleados seleccionados
            empleados_qs = form.cleaned_data.get('empleados', Empleado.objects.none())
            valor_empleados = ValorHora.objects.first()

            nombres = [f"{emp.nombre_completo}" for emp in empleados_qs]
            cedulas = [f"{emp.cedula}" for emp in empleados_qs]

            costos_empleados = [
                formato_colombia(obtener_valor_hora_por_cargo(emp, valor_empleados)) 
                if not es_contratista(emp) else "-"
                for emp in empleados_qs
            ]

            hora_comun_str = medicion.hora_inicio.strftime("%I:%M %p") if medicion.hora_inicio else "No definida"
            horas_inicio_granular = [f"{hora_comun_str}" for nombre in nombres]

            medicion.empleado_cedula = "<br>".join(cedulas)
            medicion.nombre_empleado = "<br>".join(nombres)
            medicion.hora_inicio_empleados = "<br>".join(horas_inicio_granular)
            # Guardar como una sola cadena usando <br>
            medicion.precio_hora_trabajadores = "<br>".join(costos_empleados)

            oficiales = empleados_qs.filter(cargo__icontains='oficial').exclude(cargo__icontains='contratista').count()
            ayudantes = empleados_qs.filter(cargo__icontains='ayudante').exclude(cargo__icontains='contratista').count()
            contratistas = empleados_qs.filter(cargo__icontains='contratista').count()

            if contratistas > 0:
                medicion.numero_oficiales_ayudantes = f"Contratistas: {contratistas}"
            else:
                medicion.numero_oficiales_ayudantes = f"Oficiales: {oficiales} <br> Ayudantes: {ayudantes}"

            medicion.save()

            messages.success(request, f"Medición registrada con {oficiales + ayudantes} empleados.")
            return redirect('actividad_cuadrilla')
        else:
            print("Form errors:", form.errors)
            messages.error(request, "Por favor revisa los datos del formulario.")
            return redirect('actividad_cuadrilla')
    else:
        form = MedicionInicioForm()
    return redirect('actividad_cuadrilla')

@transaction.atomic
def actualizar_cuadrilla(request, id):
    medicion = get_object_or_404(MedicionCuadrilla, id=id)
    
    if request.method == 'POST':
        try:
            registro_cambios_json = request.POST.get('registro_cambios')
            if not registro_cambios_json:
                messages.error(request, "No se recibieron datos de cambios válidos.")
                return redirect('actividad_cuadrilla')

            cambios = json.loads(registro_cambios_json)
            if not isinstance(cambios, list) or len(cambios) == 0:
                messages.error(request, "Formato de datos inválido. No se procesaron cambios.")
                return redirect('actividad_cuadrilla')

            # Listas para actualizaciones M2M
            empleados_a_remover = []  # Cédulas que salieron
            empleados_a_agregar = []  # Instancias Empleado que entraron
            historiales_creados = []

            for cambio in cambios:
                cedula = cambio.get('cedula')
                tipo = cambio.get('tipo')  # 'salio' o 'entro'
                hora_str = cambio.get('hora')
                desayuno = cambio.get('desayuno', False)  # Bool del JS, default False
                almuerzo = cambio.get('almuerzo', False)  # Bool del JS, default False

                if not all([cedula, tipo in ['salio', 'entro'], hora_str]):
                    print(f"Warning: Cambio inválido omitido: {cedula} ({tipo})")
                    continue

                try:
                    # Parsear hora a TimeField
                    hora_cambio = datetime.strptime(hora_str, "%H:%M").time()

                    # Obtener Empleado por cédula
                    empleado = get_object_or_404(Empleado, cedula=cedula)
                    usuario_obj = request.user if request.user.is_authenticated else None
                    # Crear registro de historial (uno por cambio, inmutable)
                    historial = HistorialCambiosCuadrilla(
                        medicion=medicion,
                        fecha=timezone.now().date(),
                        usuario=usuario_obj,
                        cedula_usuario=str(usuario_obj.cedula) if usuario_obj and hasattr(usuario_obj, 'cedula') else None,
                        nombre_usuario=str(usuario_obj) if usuario_obj else None
                    )

                    if tipo == 'salio':
                        historial.quien_salida = empleado
                        historial.nombre_salida = empleado.nombre_completo
                        historial.hora_salida = hora_cambio
                        empleados_a_remover.append(cedula)
                    elif tipo == 'entro':
                        historial.quien_entro = empleado
                        historial.nombre_entrada = empleado.nombre_completo
                        historial.hora_entrada = hora_cambio
                        empleados_a_agregar.append(empleado)

                    historial.save()
                    historiales_creados.append(historial)

                    # Leer comidas desde POST usando el patrón de name único
                    desayuno = request.POST.get(f"desayuno_{cedula}") == 'on'
                    almuerzo = request.POST.get(f"almuerzo_{cedula}") == 'on'

                    consumo, created = ConsumoAlimento.objects.get_or_create(
                        medicion=medicion,
                        empleado=empleado,
                    )
                    consumo.desayuno = desayuno
                    consumo.almuerzo = almuerzo
                    consumo.save()

                except ValueError as ve:
                    print(f"Warning: Hora inválida para {cedula}: {hora_str}. Omitido.")
                    continue
                except Empleado.DoesNotExist:
                    print(f"Warning: Empleado {cedula} no encontrado. Omitido.")
                    continue

            if not historiales_creados:
                messages.error(request, "No se procesó ningún cambio válido.")
                return redirect('actividad_cuadrilla')

            for empleado_entrada in empleados_a_agregar:
                if not medicion.empleados.filter(cedula=empleado_entrada.cedula).exists():
                    medicion.empleados.add(empleado_entrada)
                    # también los añadimos a la lista local para la recomputación posterior
                    
            empleados_actuales = list(medicion.empleados.all())
            empleados_unicos = []
            cedulas_seen = set()
            for emp in empleados_actuales:
                if emp and getattr(emp, 'cedula', None) and emp.cedula not in cedulas_seen:
                    empleados_unicos.append(emp)
                    cedulas_seen.add(emp.cedula)

            cedulas_finales = [str(emp.cedula) for emp in empleados_unicos]
            nombres_finales = [emp.nombre_completo for emp in empleados_unicos]

            contratistas_final = sum(1 for emp in empleados_unicos if 'contratista' in (emp.cargo or '').lower())
            oficiales_final = sum(1 for emp in empleados_unicos if 'oficial' in (emp.cargo or '').lower())
            ayudantes_final = sum(1 for emp in empleados_unicos if 'ayudante' in (emp.cargo or '').lower())

            # Si hay contratistas, usamos su conteo y ponemos "-" en otros campos
            if contratistas_final > 0:
                medicion.numero_oficiales_ayudantes = f"Contratistas: {contratistas_final}"
                medicion.precio_hora_trabajadores = "-"
                medicion.costo_total_oficiales = "-"
                medicion.costo_total_ayudantes = "-"
                medicion.costo_total_actividad = "-"
                medicion.costo_por_unidad = "-"
                medicion.diferencia_presupuestal = "-"
                medicion.comparacion_presupuestal = "-"
            
            else:
                medicion.numero_oficiales_ayudantes = f"Oficiales: {oficiales_final} <br> Ayudantes: {ayudantes_final}"
                valor_empleados = ValorHora.objects.first()
                costos_empleados = [formato_colombia(obtener_valor_hora_por_cargo(emp, valor_empleados)) for emp in empleados_unicos]
                medicion.precio_hora_trabajadores = "<br>".join(costos_empleados)

            # === ACTUALIZAR LISTA DE EMPLEADOS ===
            medicion.empleado_cedula = "<br>".join(cedulas_finales)
            medicion.nombre_empleado = "<br>".join(nombres_finales)

            # === HORAS POR EMPLEADO (detectar iniciales por SU PRIMER historial) ===
            horas_finales = []
            for emp in empleados_unicos:
                entradas = list(
                    HistorialCambiosCuadrilla.objects.filter(
                        medicion=medicion,
                        quien_entro=emp
                    ).order_by('id')
                )

                horas_emp = []

                # ---- Determinar si fue empleado inicial usando el PRIMER movimiento en historial ----
                primero = (
                    HistorialCambiosCuadrilla.objects.filter(
                        medicion=medicion
                    ).filter(
                        Q(quien_salida=emp) | Q(quien_entro=emp)
                    ).order_by('id').first()
                )

                if primero is None:
                    # Sin historial: asumimos que estaba desde el inicio (no se movió aún)
                    estaba_desde_inicio = True
                else:
                    # Si el primer registro es una SALIDA -> estaba desde inicio.
                    # Si el primer registro es una ENTRADA -> no estaba desde inicio.
                    estaba_desde_inicio = bool(primero.quien_salida and not primero.quien_entro)
                
                # 1) Si estaba desde inicio, anteponer la hora de inicio (una sola vez)
                if estaba_desde_inicio and medicion.hora_inicio:
                    horas_emp.append(medicion.hora_inicio.strftime("%I:%M %p"))

                # 2) Agregar todas las horas de ENTRADA registradas (en orden)
                for entrada in entradas:
                    if entrada.hora_entrada and hasattr(entrada.hora_entrada, "strftime"):
                        horas_emp.append(entrada.hora_entrada.strftime("%I:%M %p"))

                # 3) Caso especial: si NO estaba desde inicio y SI tiene entradas,
                #    asegurarnos de que la lista solo contenga sus horas de entrada (sin hora_inicio)
                if (not estaba_desde_inicio) and entradas:
                    horas_emp = [
                        e.hora_entrada.strftime("%I:%M %p")
                        for e in entradas
                        if e.hora_entrada
                    ]

                # 4) Si no hay datos, decidir qué mostrar
                if not horas_emp:
                    if estaba_desde_inicio and medicion.hora_inicio:
                        horas_emp.append(medicion.hora_inicio.strftime("%I:%M %p"))
                    else:
                        horas_emp.append("—")

                horas_finales.append(" - ".join(horas_emp))

            # Guardar en DB (mismo formato)
            medicion.hora_inicio_empleados = "<br>".join(horas_finales)
            medicion.save()

            # Éxito con feedback
            num_cambios = len(historiales_creados)
            messages.success(request, f"Cuadrilla actualizada. {num_cambios} cambio(s) registrado(s) en historial.")

        except Exception as e:
            messages.error(request, "Error al procesar cambios.")
            print(f"DEBUG POST Error: {e}")

        return redirect('actividad_cuadrilla')

    # GET: Renderizar modal 
    todos = Empleado.objects.filter(
        Q(cargo__icontains='oficial') |
        Q(cargo__icontains='ayudante')
    ).order_by("nombre_completo")

    activos = []
    inactivos = []

    for emp in todos:
        # Buscar último movimiento del empleado en el historial
        ultimo = HistorialCambiosCuadrilla.objects.filter(
            medicion=medicion
        ).filter(
            Q(quien_salida=emp) | Q(quien_entro=emp)
        ).order_by('-id').first()

        if ultimo:
            # Si el último movimiento fue SALIDA → inactivo
            if ultimo.quien_salida_id == emp.cedula:
                inactivos.append(emp)
            else:
                # Último movimiento fue ENTRADA → activo
                activos.append(emp)
        else:
            # No tiene historial → se evalúa exclusivamente con el M2M
            if medicion.empleados.filter(cedula=emp.cedula).exists():
                activos.append(emp)
            else:
                inactivos.append(emp)

    context = {
        "medicion": medicion,
        "empleados_en_cuadrilla": activos,
        "empleados_fuera_cuadrilla": inactivos
    }

    return render(request, 'medicion_rendimiento/actualizar_cuadrilla.html', context)

def procesos(medicion):

    cedulas_raw = (medicion.empleado_cedula or "").split("<br>")
    cedulas = [c.strip() for c in cedulas_raw if c.strip()]

    empleados_ordenados = []

    for ced in cedulas:
        try:
            empleados_ordenados.append(Empleado.objects.get(cedula=ced))
        except Empleado.DoesNotExist:
            print(f">>> WARN: cédula no encontrada: {ced}")

    restantes = [
        e for e in medicion.empleados.all()
        if e.cedula not in set(cedulas)
    ]
    empleados_ordenados.extend(restantes)

    solo_contratistas = (
        empleados_ordenados
        and all("contratista" in (e.cargo or "").lower() for e in empleados_ordenados)
    )

    cantidad_contratistas = len(empleados_ordenados) if solo_contratistas else 0

    fecha = medicion.fecha
    resultado_final = []

    total_horas_trabajadas = Decimal("0.00") 

    # 2) Procesar cada empleado
    for emp in empleados_ordenados:
        movimientos = HistorialCambiosCuadrilla.objects.filter(
            medicion=medicion
        ).filter(
            Q(quien_entro=emp) | Q(quien_salida=emp)
        ).order_by("id")

        print(f">>> Movimientos encontrados: {movimientos.count()}")
        for m in movimientos:
            print(
                f"    id={m.id} "
                f"entro={getattr(m.quien_entro,'cedula',None)} {m.hora_entrada} | "
                f"salio={getattr(m.quien_salida,'cedula',None)} {m.hora_salida}"
            )

        minutos_totales = 0

        # 3) Cálculo del tiempo trabajado
        if not movimientos.exists():
            # Nunca se movió → trabajó toda la actividad
            if medicion.hora_inicio and medicion.hora_fin:
                dt_i = datetime.combine(fecha, medicion.hora_inicio.replace(second=0, microsecond=0))
                dt_f = datetime.combine(fecha, medicion.hora_fin.replace(second=0, microsecond=0))
                minutos_totales = int((dt_f - dt_i).total_seconds() // 60)
                print(f">>> Sin historial → {minutos_totales} min")

        else:
            events = []

            for mov in movimientos:
                if mov.hora_entrada and mov.quien_entro == emp:
                    events.append(("entrada", mov.hora_entrada.replace(second=0, microsecond=0)))
                if mov.hora_salida and mov.quien_salida == emp:
                    events.append(("salida", mov.hora_salida.replace(second=0, microsecond=0)))

            # Orden real por hora
            events.sort(key=lambda x: x[1])
            print(">>> Events ORDENADOS:", events)

            pares = []
            entrada_actual = None

            #  Caso clave: primer evento es SALIDA → estaba desde hora_inicio
            if events and events[0][0] == "salida" and medicion.hora_inicio:
                entrada_actual = medicion.hora_inicio.replace(second=0, microsecond=0)
                print(">>> Entrada implícita desde hora_inicio:", entrada_actual)

            for tipo, hora in events:
                if tipo == "entrada":
                    entrada_actual = hora

                elif tipo == "salida":
                    if entrada_actual:
                        pares.append((entrada_actual, hora))
                        entrada_actual = None
                    else:
                        print(f">>> WARN: salida sin entrada previa {hora}")

            # Cerrar entrada abierta con hora_fin
            if entrada_actual and medicion.hora_fin:
                pares.append(
                    (entrada_actual, medicion.hora_fin.replace(second=0, microsecond=0))
                )
                print(">>> Cerrando entrada abierta con hora_fin")

            print(">>> Pares entrada → salida:", pares)

            for ent, sal in pares:
                dt_e = datetime.combine(fecha, ent)
                dt_s = datetime.combine(fecha, sal)
                diff = int((dt_s - dt_e).total_seconds() // 60)
                minutos_totales +=int((dt_s - dt_e).total_seconds() // 60)
                print(f"    tramo {ent} → {sal} = {diff} min")

        # 4) Descuentos por comidas
        desayuno = False
        almuerzo = False

        try:
            consumo = ConsumoAlimento.objects.get(medicion=medicion, empleado=emp)
            desayuno = bool(consumo.desayuno)
            almuerzo = bool(consumo.almuerzo)
            print(f">>> ConsumoAlimento → desayuno={desayuno}, almuerzo={almuerzo}")
        except ConsumoAlimento.DoesNotExist:
            pass

        if desayuno:
            minutos_totales -= 30
        if almuerzo:
            minutos_totales -= 60

        minutos_totales = max(minutos_totales, 0)

        horas = (Decimal(minutos_totales) / Decimal(60)).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )

        resultado_final.append(f"{float(horas):.2f} h")
        total_horas_trabajadas += horas 

        print(f">>> RESULTADO {emp.cedula}: {minutos_totales} min → {horas} h")

    # 5) CÁLCULO COSTOS TOTALES POR CARGO
    valor_empleados = ValorHora.objects.first()

    costo_total_oficiales = Decimal("0.00")
    costo_total_ayudantes = Decimal("0.00")
    precio_total_horas = Decimal("0.00")

    if not solo_contratistas:
        for emp, horas_txt in zip(empleados_ordenados, resultado_final):

            horas_decimal = Decimal(horas_txt.replace(" h", ""))

            costo_hora = Decimal(obtener_valor_hora_por_cargo(emp, valor_empleados))
            costo_real = (costo_hora * horas_decimal).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            cargo = (emp.cargo or "").lower()

            if "oficial" in cargo:
                costo_total_oficiales += costo_real
            elif "ayudante" in cargo:
                costo_total_ayudantes += costo_real

            precio_total_horas += costo_real

            print(
                f">>> COSTO {emp.cedula} | {cargo}: "
                f"{horas_decimal}h × {costo_hora} = {costo_real}"
            )

    # 6) RENDIMIENTO REAL
    rendimiento_real = None

    cantidad = Decimal(str(round(medicion.cantidad_producida or 0, 4)))
    horas_totales = total_horas_trabajadas

    if cantidad and horas_totales and horas_totales > 0:
        rendimiento_real = (cantidad / horas_totales).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    else:
        print(">>> Rendimiento real NO calculado (valores inválidos)")

    # 7) Costo por unidad de medida
    costo_por_unidad = None

    if not solo_contratistas and cantidad and cantidad > 0:

        costo_por_unidad = (precio_total_horas / cantidad).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        print(f">>> Costo por unidad: {precio_total_horas} / {cantidad} = {costo_por_unidad}")

    else:
        costo_por_unidad = None
        print(">>> Costo por unidad NO calculado (cantidad inválida)")

    # 8) COMPARACIÓN PROGRAMADA Y PRESUPUESTAL (%)

    comparacion_programado = None
    comparacion_presupuestal = None
    diferencia_presupuestal = None

    cumplimiento_presupuestal = None
    cumplimiento_programado = None

    rend_real = rendimiento_real
    costo_unidad = costo_por_unidad

    try:
        cumplimiento = Cumplimiento.objects.get(actividad__iexact=medicion.actividad)
    except Cumplimiento.DoesNotExist:
        cumplimiento = None
        print(">>> Cumplimiento NO encontrado para actividad:", medicion.actividad)

    if cumplimiento and rend_real and rend_real > 0:  
        if cumplimiento.cumplimiento_programado and cumplimiento.cumplimiento_programado > 0:
            comparacion_programado = (
                rend_real / Decimal(cumplimiento.cumplimiento_programado) * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            cumplimiento_programado = cumplimiento.cumplimiento_programado

    if cumplimiento and costo_unidad and costo_unidad > 0:
        diferencia_presupuestal = Decimal("0.00")

        if cumplimiento.cumplimiento_presupuestal and cumplimiento.cumplimiento_presupuestal > 0:
            diferencia_presupuestal = (cumplimiento.cumplimiento_presupuestal - costo_unidad).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

            comparacion_presupuestal = ( 
                (cumplimiento.cumplimiento_presupuestal / costo_unidad) * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            cumplimiento_presupuestal = cumplimiento.cumplimiento_presupuestal

    # 9) Guardar resultado final
    medicion.horas_efectivas_trabajador = "<br>".join(resultado_final)
    medicion.horas_trabajadas_totales = total_horas_trabajadas
    medicion.costo_total_oficiales = costo_total_oficiales
    medicion.costo_total_ayudantes = costo_total_ayudantes
    medicion.precio_total_horas = precio_total_horas
    medicion.rendimiento_real = rendimiento_real
    medicion.comparacion_programado = comparacion_programado
    medicion.diferencia_presupuestal = diferencia_presupuestal
    medicion.comparacion_presupuestal = comparacion_presupuestal
    medicion.costo_por_unidad = costo_por_unidad
    medicion.cumplimiento_presupuestal = cumplimiento_presupuestal
    medicion.cumplimiento_programado = cumplimiento_programado

    if solo_contratistas:
        medicion.costo_total_oficiales = None
        medicion.costo_total_ayudantes = None
        medicion.precio_total_horas = None
        medicion.costo_por_unidad = None
        medicion.diferencia_presupuestal = None
        medicion.comparacion_presupuestal = None
        medicion.numero_oficiales_ayudantes = f"Contratistas: {cantidad_contratistas}"

    medicion.save(update_fields=[
        "horas_efectivas_trabajador",
        "horas_trabajadas_totales",
        "costo_total_oficiales",
        "costo_total_ayudantes",
        "precio_total_horas",
        "rendimiento_real",
        "diferencia_presupuestal",
        "comparacion_programado",
        "comparacion_presupuestal",
        "costo_por_unidad",
        "cumplimiento_presupuestal",
        "cumplimiento_programado",
    ])

    print(">>> PROCESO FINALIZADO:", medicion.horas_efectivas_trabajador)

def registrar_fin_medicion(request, id):
    if request.method == 'POST':
        medicion = get_object_or_404(MedicionCuadrilla, id=id)

        try:
            print("DEBUG registrar_fin_medicion: inicio para medicion id=", medicion.id)

            # === ZONA BLINDADA: MANEJO DE FOTO ===
            if "foto_fin" in request.FILES:
                # Si ya hay foto, intentamos 'olvidarla' antes de poner la nueva
                # para evitar conflictos de rutas, pero SIN borrarla del disco (dejamos que AWS maneje eso)
                if medicion.foto_fin:
                    print(f"Reemplazando foto anterior: {medicion.foto_fin.name}")
                
                medicion.foto_fin = request.FILES["foto_fin"]
            # =====================================

            cantidad_producida = float(request.POST.get('cantidad_producida', 0))
            hora_fin_str = request.POST.get('hora_fin')

            if not hora_fin_str:
                messages.error(request, "Debe ingresar la hora de finalización.")
                return redirect('actividad_cuadrilla')

            # 1) Guardar hora fin y cantidad producida
            hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()
            medicion.hora_fin = hora_fin
            medicion.cantidad_producida = cantidad_producida

            # 2) Guardar consumos de alimento
            desayuno = request.POST.get('desayuno') == 'on'
            almuerzo = request.POST.get('almuerzo') == 'on'

            if desayuno or almuerzo:
                for empleado in medicion.empleados.all():
                    tiene_historial = HistorialCambiosCuadrilla.objects.filter(
                        medicion=medicion
                    ).filter(
                        Q(quien_entro=empleado) | Q(quien_salida=empleado)
                    ).exists()

                    if tiene_historial:
                        continue

                    consumo, _ = ConsumoAlimento.objects.get_or_create(
                        medicion=medicion,
                        empleado=empleado
                    )
                    if desayuno:
                        consumo.desayuno = True
                    if almuerzo:
                        consumo.almuerzo = True
                    consumo.save()

            # 3) Hora fin por empleado (visual)
            horas_fin_por_empleado = []
            empleados_qs = list(medicion.empleados.all())

            existe_historial = HistorialCambiosCuadrilla.objects.filter(
                medicion=medicion
            ).exists()

            for emp in empleados_qs:
                if not existe_historial:
                    hora_para_emp = medicion.hora_fin.strftime("%I:%M %p")
                else:
                    movimientos = HistorialCambiosCuadrilla.objects.filter(
                        medicion=medicion
                    ).filter(
                        Q(quien_entro=emp) | Q(quien_salida=emp)
                    ).order_by('id')

                    if not movimientos.exists():
                        hora_para_emp = medicion.hora_fin.strftime("%I:%M %p")
                    else:
                        events = []
                        for mov in movimientos:
                            if mov.quien_salida and mov.hora_salida:
                                events.append(("salida", mov.hora_salida, mov.id))
                            if mov.quien_entro and mov.hora_entrada:
                                events.append(("entrada", mov.hora_entrada, mov.id))

                        events.sort(key=lambda x: x[2])
                        last_event_type = events[-1][0]
                        salidas = [e for e in events if e[0] == "salida"]

                        hora_fin_fmt = medicion.hora_fin.strftime("%I:%M %p")

                        if not salidas:
                            hora_para_emp = hora_fin_fmt
                        else:
                            partes = []
                            for i, (_, hora_salida, _) in enumerate(salidas):
                                salida_fmt = hora_salida.strftime("%I:%M %p")

                                if last_event_type == "entrada" and i == len(salidas) - 1:
                                    partes.append(f"{salida_fmt} - {hora_fin_fmt}")
                                else:
                                    partes.append(salida_fmt)

                            hora_para_emp = " ".join(partes)

                horas_fin_por_empleado.append(hora_para_emp)

            medicion.hora_fin_empleados = "<br>".join(horas_fin_por_empleado)

            # 4) Guardar y ejecutar procesos
            medicion.save()
            procesos(medicion)

            messages.success(request, "Registro finalizado correctamente.")
            print("DEBUG registrar_fin_medicion: medicion guardada exitosamente.")

        except Exception as e:
            print("Error al registrar fin:", e)
            messages.error(request, f"Ocurrió un error al finalizar: {str(e)}")

    return redirect('actividad_cuadrilla')

def registrar_cumplimiento(request):
    if request.method == 'POST':
        actividad = request.POST.get('actividad', '').lower().strip()
        unidad_medida = request.POST.get('unidad_medida')

        raw_presupuestal = request.POST.get('cumplimiento_presupuestal', '0')
        clean_presupuestal = re.sub(r'[^\d]', '', raw_presupuestal)

        if not clean_presupuestal:
            clean_presupuestal = '0'
        
        cumplimiento_presupuestal = Decimal(clean_presupuestal)
        cumplimiento_programado = Decimal(request.POST.get('cumplimiento_programado', '0'))

        # Buscar si la actividad ya existe (independiente de mayúsculas)
        cumplimiento_existente = Cumplimiento.objects.filter(actividad__iexact=actividad).first()

        try:
            if cumplimiento_existente:
                # Si los valores son 0 → eliminar la actividad
                if cumplimiento_presupuestal == 0 and cumplimiento_programado == 0:
                    cumplimiento_existente.delete()
                    messages.success(request, f"La actividad '{actividad}' fue eliminada (valores en 0).")

                else:
                    # Actualizar valores existentes
                    cumplimiento_existente.unidad_medida = unidad_medida
                    cumplimiento_existente.cumplimiento_presupuestal = cumplimiento_presupuestal
                    cumplimiento_existente.cumplimiento_programado = cumplimiento_programado
                    cumplimiento_existente.save()
                    messages.success(request, f"Actividad '{actividad}' actualizada correctamente.")

            else:
                # Si no existe y los valores son mayores a 0 → crear nueva
                if cumplimiento_presupuestal > 0 or cumplimiento_programado > 0:
                    Cumplimiento.objects.create(
                        actividad=actividad,
                        unidad_medida=unidad_medida,
                        cumplimiento_presupuestal=cumplimiento_presupuestal,
                        cumplimiento_programado=cumplimiento_programado
                    )
                    messages.success(request, f"Actividad '{actividad}' registrada exitosamente.")
                else:
                    messages.warning(request, f"No se registró la actividad '{actividad}' porque sus valores son 0.")

        except Exception as e:
            messages.error(request, f"Ocurrió un error al guardar la actividad: {e}")

    return redirect('actividad_cuadrilla')

def calcular_estado(porcentaje):
    if porcentaje < 80:
        return "bajo"
    elif 80 <= porcentaje <= 100:
        return "bien"
    else:
        return "excelente"

def api_demanda_empleados(request):
    proyecto = request.GET.get("proyecto", "Ciudadela Andina")
    modo = request.GET.get("modo", "mes")  # 👈 POR DEFECTO MES

    hoy = timezone.now().date()
    fecha_fin = request.GET.get("fecha_fin", hoy)
    fecha_inicio = request.GET.get("fecha_inicio", hoy - timedelta(days=180))

    # Normalizar fechas si vienen como string
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    if isinstance(fecha_fin, str):
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    data = demanda_empleados_por_actividad(
        proyecto=proyecto,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo=modo
    )

    return JsonResponse(data)


def reporte_cuadrilla (request):
    proyecto = request.GET.get('proyecto', 'Ciudadela Andina')
    actividad_get = request.GET.get('actividad')

    hoy = timezone.now().date()
    fecha_fin = request.GET.get('fecha_fin', hoy)
    fecha_inicio = request.GET.get('fecha_inicio', hoy - timedelta(days=30))

    cumplimiento = None
    unidad_medida = None
    cumplimiento_programado = Decimal('0.00')
    cumplimiento_presupuestal = Decimal('0.00')

    # Normalizar fechas si vienen como string
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    if isinstance(fecha_fin, str):
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    mediciones_base = MedicionCuadrilla.objects.filter(
        proyecto=proyecto,
        fecha__range=(fecha_inicio, fecha_fin),
    )

    actividades = (
        mediciones_base
        .values_list('actividad', flat=True)
        .distinct()
        .order_by('actividad')
    )

    if actividad_get:
        actividad_final = actividad_get
    else:
        actividad_dominante = (
            mediciones_base
            .values('actividad')
            .annotate(total=Count('id'))
            .order_by('-total')
            .first()
        )
        actividad_final = actividad_dominante['actividad'] if actividad_dominante else None

    if actividad_final:
        mediciones = mediciones_base.filter(actividad=actividad_final, hora_fin__isnull=False)

        cumplimiento = Cumplimiento.objects.filter(
            actividad__iexact=actividad_final
        ).first()

        if cumplimiento:
            unidad_medida = cumplimiento.unidad_medida
            cumplimiento_programado = cumplimiento.cumplimiento_programado
            cumplimiento_presupuestal = cumplimiento.cumplimiento_presupuestal

            print ('cumplimiento_programado:', cumplimiento_programado)
            print ('cumpliemiento_presupuestal:', cumplimiento_presupuestal)

    else:
        mediciones = mediciones_base.filter(hora_fin__isnull=False)
    
    # KPI: Cumplimiento Presupuestal y cumplimiento programado
    promedio_presupuestal = (
        mediciones
        .aggregate(promedio = Avg('comparacion_presupuestal'))
        ['promedio'] or Decimal ('0')
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    promedio_programado = (
        mediciones
        .aggregate(promedio = Avg ('comparacion_programado'))
        ['promedio'] or Decimal ('0')
    ).quantize (Decimal('0.01'), rounding=ROUND_HALF_UP)

    promedio_rendimiento_real = (
        mediciones
        .aggregate(promedio = Avg ('rendimiento_real'))
        ['promedio'] or Decimal ('0')
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    promedio_costo_por_unidad = (
        mediciones
        .aggregate(promedio = Avg ('costo_por_unidad'))
        ['promedio'] or Decimal ('0')
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    estado_presupuestal = calcular_estado (promedio_presupuestal)
    estado_programado = calcular_estado (promedio_programado)

    cumplimiento_presupuestal_width = float(min(promedio_presupuestal, Decimal('100')))
    cumplimiento_programado_width = float(min(promedio_programado, Decimal('100')))

    labels_rendimiento, data_rendimiento = rendimiento_real_mensual(
        proyecto=proyecto,
        actividad=actividad_final
    )

    graficos_cuadrillas = rendimiento_real_diario_por_cuadrilla(
        proyecto=proyecto,
        actividad=actividad_final,
        fecha_fin=fecha_fin,
        fecha_inicio=fecha_fin - timedelta(days=6),
    )

    graficos_costo_cuadrillas = costo_por_unidad_diario_por_cuadrilla(
        proyecto=proyecto,
        actividad=actividad_final,
        fecha_fin=fecha_fin,
        fecha_inicio=fecha_fin - timedelta(days=6),
    )

    demanda_personal = demanda_empleados_por_actividad(
        proyecto=proyecto,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )

    mediciones_qs = MedicionCuadrilla.objects.filter(
        proyecto=proyecto,
        actividad=actividad_final
    )
    
    diagnostico_rendimiento = diagnostico_rendimiento_real(
        mediciones_qs=mediciones_qs
    )

    costo_presupuestado = (
        cumplimiento.cumplimiento_presupuestal
        if cumplimiento and cumplimiento.cumplimiento_presupuestal
        else None
    )

    diagnostico_costo = diagnostico_costo_por_unidad(
        registros=mediciones_qs,
        presupuesto_unitario=costo_presupuestado
    )
    
    if actividad_final:
        comparativo_data = comparativo_rendimiento_cuadrillas(
            proyecto=proyecto,
            actividad=actividad_final,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
    else:
        # Estructura vacía segura para evitar errores en JS si no hay actividad
        comparativo_data = {
            "labels": [], "data": [], 
            "thresholds": {"bajo": 0, "estandar": 0, "superior": 0},
            "integrantes": []
        }

    cronograma_data = cronograma_actividades(
        proyecto=proyecto,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

    context = {
        "comparacion_presupuestal": promedio_presupuestal,
        "comparacion_programado": promedio_programado,
        "promedio_rendimiento_real": promedio_rendimiento_real,
        "promedio_costo_por_unidad": promedio_costo_por_unidad,
        "cumplimiento_presupuestal_width": cumplimiento_presupuestal_width,
        "cumplimiento_programado_width": cumplimiento_programado_width,
        "estado_presupuestal": estado_presupuestal,
        "estado_programado": estado_programado,
        "unidad_medida": unidad_medida if actividad_final and cumplimiento else None,
        "cumplimiento_programado": cumplimiento_programado if actividad_final and cumplimiento else None,
        "cumplimiento_presupuestal": cumplimiento_presupuestal if actividad_final and cumplimiento else None,
        "proyecto": proyecto, 
        "actividad": actividad_final,
        "actividades": actividades,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "labels_rendimiento": labels_rendimiento,
        "data_rendimiento": data_rendimiento,
        "graficos_cuadrillas": graficos_cuadrillas,
        "graficos_cuadrillas_json": json.dumps(graficos_cuadrillas),
        "graficos_costo_cuadrillas": graficos_costo_cuadrillas,
        "graficos_costo_cuadrillas_json": json.dumps(graficos_costo_cuadrillas),
        "DEMANDA_PERSONAL": json.dumps(demanda_personal),
        "diagnostico_rendimiento": json.dumps(diagnostico_rendimiento),
        "diagnostico_costo": json.dumps(diagnostico_costo),
        "comparativo_cuadrillas_json": json.dumps(comparativo_data),
        "cronograma_data_json": json.dumps(cronograma_data, default=str),
    }

    print("DEMANDA_PERSONAL >>>", demanda_personal)


    return render (request, 'medicion_rendimiento/reporte_cuadrilla.html', context)


# Medicion de rendimiento indicidual

def medicion_individual(request):
    return render(request, 'medicion_rendimiento/medicion_individual.html')

def guardar_configuracion_alertas(request):
    if request.method == 'POST':
        tipo_alerta = request.POST.get('tipo_alerta')
        usuario_ids = request.POST.getlist('destinatarios') # Obtenemos la lista de IDs seleccionados

        if not usuario_ids:
            messages.warning(request, "Debe seleccionar al menos un usuario.")
            return redirect('actividad_cuadrilla')

        # Obtenemos el modelo de usuario para buscar sus datos
        User = get_user_model()
        contador_registros = 0

        for uid in usuario_ids:
            try:
                user_obj = User.objects.get(id=uid)
                
                # Verificamos si ya existe este usuario específico para este tipo de alerta
                # Esto evita que una persona tenga 2 veces el mismo tipo de alerta (tu preocupación anterior)
                existe = ConfiguracionAlerta.objects.filter(
                    tipo_alerta=tipo_alerta, 
                    destinatarios=user_obj
                ).exists()

                if not existe:
                    # 1. Creamos un nuevo registro independiente
                    nueva_alerta = ConfiguracionAlerta.objects.create(
                        tipo_alerta=tipo_alerta,
                        nombre_usuario=user_obj.nombre_completo,
                        correo=user_obj.correo if hasattr(user_obj, 'correo') else user_obj.email
                    )
                    
                    # 2. Asociamos al usuario a este registro específico
                    nueva_alerta.destinatarios.add(user_obj)
                    contador_registros += 1
                    
            except User.DoesNotExist:
                continue

        if contador_registros > 0:
            messages.success(request, f"Se crearon {contador_registros} registros individuales exitosamente.")
        else:
            messages.info(request, "Los usuarios seleccionados ya tienen esta alerta configurada.")

    return redirect('actividad_cuadrilla')
    
def eliminar_alerta(request, alerta_id):
    alerta = get_object_or_404(ConfiguracionAlerta, id=alerta_id)
    alerta.delete()
    messages.success(request, "Asignación eliminada correctamente.")
    return redirect('actividad_cuadrilla')