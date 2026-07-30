import os
import io
import json
import re
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, Dict, List

import pandas as pd

from django.conf import settings
from django.db import transaction

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .models import Empleado
from core.sincronizacion_actividades import procesar_actividades_excel



# CONFIGURACIÓN
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

SPANISH_MONTHS = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# GOOGLE DRIVE
def get_drive_service():
    # Intentamos obtener las credenciales de la variable de entorno (Producción)
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    
    if creds_json:
        # Si existe la variable, cargamos el JSON directamente desde el texto
        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            info, 
            scopes=SCOPES
        )
    else:
        # Si no existe (Local), usamos el archivo como siempre
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_FILE,
            scopes=SCOPES
        )
        
    return build("drive", "v3", credentials=creds, cache_discovery=False)
    
def list_folder(service, folder_id: str) -> List[Dict]:
    items, page_token = [], None
    while True:
        resp = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType)",
            pageSize=200,
            pageToken=page_token
        ).execute()
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def find_year_folder(service, root_id: str, year: int):
    for f in list_folder(service, root_id):
        if f["mimeType"].endswith("folder") and str(year) in f["name"]:
            return f
    return None


def find_month_folder(service, year_id: str, month: int):
    month_name = SPANISH_MONTHS[month]
    for f in list_folder(service, year_id):
        if f["mimeType"].endswith("folder") and month_name in f["name"].lower():
            return f
    return None


def pick_quincena_file(files: List[Dict], quincena: str):
    for f in files:
        if quincena.lower() in f["name"].lower():
            return f
    return None


def download_file(service, file_meta: Dict, dest: str):
    if file_meta["mimeType"] == "application/vnd.google-apps.spreadsheet":
        request = service.files().export_media(
            fileId=file_meta["id"],
            mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        request = service.files().get_media(fileId=file_meta["id"])

    with io.FileIO(dest, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


# UTILIDADES
def determine_quincena(date: datetime) -> str:
    return "1Q" if date.day <= 15 else "2Q"


def clean_money(value) -> Optional[Decimal]:
    if value is None:
        return None

    if isinstance(value, float) and pd.isna(value):
        return None

    try:
        text = str(value).strip()

        # Quitar cualquier cosa que no sea número, coma o punto
        text = re.sub(r"[^\d.,]", "", text)

        if not text:
            return None

        # Formato colombiano: 1.234.567,89
        if "." in text and "," in text:
            text = text.replace(".", "").replace(",", ".")

        return (
            Decimal(text)
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )

    except (InvalidOperation, ValueError):
        return None


def extraer_valores_hora(df: pd.DataFrame) -> Dict[str, Decimal]:
    fila_header = None

    # Buscar celda combinada en columna K (índice 10)
    for i in range(len(df)):
        cell = str(df.iloc[i, 10]).lower().strip()
        if "valor hora" in cell:
            fila_header = i
            break

    if fila_header is None:
        raise ValueError("No se encontró 'VALOR HORA DE EMPLEADOS'")

    # Los valores están DOS filas debajo
    fila_valores = fila_header + 2

    valores = {
        "ayudante_raso": clean_money(df.iloc[fila_valores, 10]),      # K
        "ayudante_entendido": clean_money(df.iloc[fila_valores, 11]), # L
        "oficial_junior": clean_money(df.iloc[fila_valores, 12]),     # M
        "oficial_senior": clean_money(df.iloc[fila_valores, 13]),     # N
    }

    if any(v is None for v in valores.values()):
        raise ValueError("Valores hora incompletos o mal formateados")

    return valores


# FUNCIÓN PRINCIPAL
def fetch_and_store_empleados(root_folder_id: str):

    service = get_drive_service()
    today = datetime.today()

    year = today.year
    month = today.month
    quincena = determine_quincena(today)

    print(f"🗓️ Fecha actual: {today.date()}")
    print(f"📁 Año: {year} | Mes: {SPANISH_MONTHS[month]} | Quincena: {quincena}")

    year_folder = find_year_folder(service, root_folder_id, year)
    if not year_folder:
        raise Exception("No se encontró carpeta del año")

    month_folder = find_month_folder(service, year_folder["id"], month)
    if not month_folder:
        raise Exception("No se encontró carpeta del mes")

    files = list_folder(service, month_folder["id"])
    file_meta = pick_quincena_file(files, quincena)
    if not file_meta:
        raise Exception("No se encontró archivo de quincena")

    tmp_path = os.path.join(tempfile.gettempdir(), "empleados.xlsx")
    download_file(service, file_meta, tmp_path)

# ---------------- EMPLEADOS ----------------
    df_emp = pd.read_excel(tmp_path, sheet_name="Cargos")
    df_emp.columns = df_emp.columns.str.lower().str.strip()

    col_cc = next((c for c in df_emp.columns if 'cc' in c or 'cedula' in c), None)
    col_nombre = next((c for c in df_emp.columns if 'nombre' in c), None)
    col_cargo = next((c for c in df_emp.columns if 'cargo' in c), None)
    col_costos = next((c for c in df_emp.columns if 'costo' in c or 'salario' in c), None)
    col_ubicacion = next((c for c in df_emp.columns if 'ubicaci' in c), None)

    if not col_cc:
        raise Exception(f"No se encontró columna de Cédula. Columnas: {list(df_emp.columns)}")

    # Limpieza estricta de cédulas
    df_emp = df_emp.dropna(subset=[col_cc])
    df_emp[col_cc] = df_emp[col_cc].astype(str).str.replace(r'[^\d]', '', regex=True)
    df_emp = df_emp[df_emp[col_cc] != '']
    df_emp = df_emp[df_emp[col_cc].str.isnumeric()]

    cedulas_excel = []
    
    # Contadores para la auditoría en tiempo real
    nuevos_count = 0
    actualizados_count = 0

    with transaction.atomic():
        for _, row in df_emp.iterrows():
            cedula_limpia = str(row[col_cc])
            valor_nombre = str(row[col_nombre]).strip() if col_nombre and pd.notna(row[col_nombre]) else "Sin Nombre"
            valor_cargo = str(row[col_cargo]).strip() if col_cargo and pd.notna(row[col_cargo]) else "Sin Cargo"
            valor_salario = clean_money(row[col_costos]) if col_costos and pd.notna(row[col_costos]) else Decimal('0.00')
            valor_ubicacion = str(row[col_ubicacion]).strip() if col_ubicacion and pd.notna(row[col_ubicacion]) else ""
            
            cedulas_excel.append(cedula_limpia)

            # 🔎 AUDITORÍA: Buscamos si el empleado ya existe en el sistema
            empleado_db = Empleado.objects.filter(cedula=cedula_limpia).first()

            if not empleado_db:
                # 🟩 CASO 1: Es un empleado nuevo
                Empleado.objects.create(
                    cedula=cedula_limpia,
                    nombre_completo=valor_nombre,
                    cargo=valor_cargo,
                    salario=valor_salario,
                    ubicacion=valor_ubicacion
                )
                nuevos_count += 1
                print(f"✨ [NUEVO] Empleado creado: {valor_nombre} (CC: {cedula_limpia})")
            else:
                # 🟨 CASO 2: Ya existe, verificamos si cambió ALGUN dato en el Excel
                hubo_cambio = (
                    empleado_db.nombre_completo != valor_nombre or
                    empleado_db.cargo != valor_cargo or
                    empleado_db.salario != valor_salario or
                    empleado_db.ubicacion != valor_ubicacion
                )
                
                if hubo_cambio:
                    # Registramos qué cambió exactamente para los logs internos
                    print(f"🔄 [ACTUALIZACIÓN] Detectados cambios para CC: {cedula_limpia}")
                    
                    empleado_db.nombre_completo = valor_nombre
                    empleado_db.cargo = valor_cargo
                    empleado_db.salario = valor_salario
                    empleado_db.ubicacion = valor_ubicacion
                    empleado_db.save()
                    actualizados_count += 1

        # 🟥 CASO 3: Eliminamos de la BD a quienes ya no aparecen en el Excel de Drive
        eliminados_count, _ = Empleado.objects.exclude(cedula__in=cedulas_excel).delete()
        if eliminados_count > 0:
            print(f"🗑️ [ELIMINACIÓN] Se borraron {eliminados_count} empleados que ya no figuran en Drive.")

        
    # LLAMAMOS AL CORE PARA SINCRONIZAR LAS ACTIVIDADES CON EL MISMO EXCEL
    try:
        procesar_actividades_excel(tmp_path)
    except Exception as e:
        print(f"❌ Error en el CORE al sincronizar actividades: {e}")

    resumen = f"Sincronización Empleados: {nuevos_count} nuevos, {actualizados_count} actualizados, {eliminados_count} eliminados."
    print(f"📊 {resumen}")
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    # El reporte detallado final que devolverá Celery o la vista manual
    resumen = f"Proceso completado con éxito: {nuevos_count} nuevos, {actualizados_count} actualizados, {eliminados_count} eliminados."
    print(f"📊 RESUMEN SINCRONIZACIÓN: {resumen}")
    return resumen
"""
EJECUCIÓN:
python manage.py shell
from personal.scheduler import scheduled_fetch
scheduled_fetch()
"""
