import pandas as pd
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db import transaction
from medicion_rendimiento.models import Cumplimiento 
from proyectos.models import Proyecto

def limpiar_numero(val):
    if pd.isna(val): return Decimal('0.00')
    val_str = str(val).strip().replace(',', '.')
    val_str = re.sub(r'[^\d.]', '', val_str) 
    try:
        return Decimal(val_str)
    except InvalidOperation:
        return Decimal('0.00')

def procesar_actividades_excel(tmp_path):
    with pd.ExcelFile(tmp_path) as xls:
        hojas_excel = xls.sheet_names
        proyectos_db = Proyecto.objects.all()

        for proyecto in proyectos_db:
            # Limpiamos espacios invisibles tanto en la BD como en el Excel
            nombre_esperado = f"actividades {proyecto.nombre.strip().lower()}"
            hoja_encontrada = next((h for h in hojas_excel if h.strip().lower() == nombre_esperado), None)

            if not hoja_encontrada:
                print(f"⚠️ [OMITIDO] No encontré pestaña para el proyecto '{proyecto.nombre}'. Buscaba: '{nombre_esperado}'. Pestañas reales en el Excel: {hojas_excel}")
                continue

            print(f"✅ Pestaña encontrada: '{hoja_encontrada}'. Procesando...")

            # 🔥 CAMBIO 2: Leemos directamente del 'xls' abierto en lugar de pasarle la ruta de nuevo. 
            # ¡Esto hace que el sistema sea el doble de rápido!
            df_act = pd.read_excel(xls, sheet_name=hoja_encontrada)
            df_act.columns = df_act.columns.str.lower().str.strip()

            col_desc = next((c for c in df_act.columns if 'nombre' in c or 'actividad' in c), None)
            col_und = next((c for c in df_act.columns if 'unidad' in c or 'medida' in c), None)
            col_presup = next((c for c in df_act.columns if 'presupuestal' in c or 'presupuesto' in c), None)
            col_prog = next((c for c in df_act.columns if 'programado' in c or 'programa' in c), None)
            col_estado = next((c for c in df_act.columns if 'estado' in c), None)

            if not col_desc:
                print(f"❌ ERROR: No encontré la columna de la actividad en '{hoja_encontrada}'. Columnas leídas: {list(df_act.columns)}")
                continue

            actividades_validas_excel = []
            agregadas = 0
            omitidas_cero = 0

            with transaction.atomic():
                for _, row in df_act.iterrows():
                    act_nombre = str(row[col_desc]).strip()
                    if not act_nombre or act_nombre.lower() == 'nan':
                        continue

                    estado = str(row[col_estado]).strip().lower() if col_estado and pd.notna(row[col_estado]) else ""

                    if 'terminad' in estado or 'finaliz' in estado or 'complet' in estado:
                        Cumplimiento.objects.filter(proyecto=proyecto, actividad__iexact=act_nombre).delete()
                        continue

                    val_presup = limpiar_numero(row[col_presup]) if col_presup else Decimal('0.00')
                    val_prog_dia = limpiar_numero(row[col_prog]) if col_prog else Decimal('0.00')

                    if val_presup <= 0 and val_prog_dia <= 0:
                        Cumplimiento.objects.filter(proyecto=proyecto, actividad__iexact=act_nombre).delete()
                        omitidas_cero += 1
                        continue

                    val_prog_hora = Decimal('0.00')
                    if val_prog_dia > 0:
                        val_prog_hora = (val_prog_dia / Decimal('7.33')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                    val_presup = val_presup.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    unidad = str(row[col_und]).strip() if col_und and pd.notna(row[col_und]) else ""

                    actividades_validas_excel.append(act_nombre.lower())

                    cumplimiento_db = Cumplimiento.objects.filter(proyecto=proyecto, actividad__iexact=act_nombre).first()

                    if not cumplimiento_db:
                        Cumplimiento.objects.create(
                            proyecto=proyecto, actividad=act_nombre, unidad_medida=unidad,
                            cumplimiento_presupuestal=val_presup, cumplimiento_programado=val_prog_hora
                        )
                    else:
                        cumplimiento_db.unidad_medida = unidad
                        cumplimiento_db.cumplimiento_presupuestal = val_presup
                        cumplimiento_db.cumplimiento_programado = val_prog_hora
                        cumplimiento_db.save()
                    
                    agregadas += 1

                # Eliminar las que ya no están
                existentes = Cumplimiento.objects.filter(proyecto=proyecto)
                for ext in existentes:
                    if ext.actividad.lower() not in actividades_validas_excel:
                        ext.delete()

        print(f"📊 Resumen de '{hoja_encontrada}': {agregadas} Guardadas OK | {omitidas_cero} Omitidas por estar en $0.")