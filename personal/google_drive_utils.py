import os
import io
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

from .models import Empleado, ValorHora

# CONFIGURACIÓN
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

SPANISH_MONTHS = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# GOOGLE DRIVE
def get_drive_service():
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

    # ---------------- VALORES HORA ----------------
    df_raw = pd.read_excel(tmp_path, sheet_name="Cargos", header=None)
    valores = extraer_valores_hora(df_raw)

    print("💰 Valores hora detectados:")
    for k, v in valores.items():
        print(f"  {k}: {v}")

    ValorHora.objects.update_or_create(
        id=1,
        defaults=valores
    )

    # ---------------- EMPLEADOS ----------------
    df_emp = pd.read_excel(tmp_path, sheet_name="Cargos")
    df_emp.columns = df_emp.columns.str.lower().str.strip()

    col_cc = next((c for c in df_emp.columns if 'cc' in c or 'cedula' in c), None)
    col_nombre = next((c for c in df_emp.columns if 'nombre' in c), None)
    col_cargo = next((c for c in df_emp.columns if 'cargo' in c), None)

    if not col_cc:
        raise Exception(f"No se encontró columna de Cédula. Columnas: {list(df_emp.columns)}")

    # 3. Limpieza de Cédula (Deja SOLO los números)
    df_emp[col_cc] = df_emp[col_cc].astype(str)
    
    # Esta línea elimina CC, espacios, puntos y comas de un solo golpe
    df_emp[col_cc] = df_emp[col_cc].str.replace(r'[^\d]', '', regex=True)
    
    # Filtramos para quitar filas que quedaron vacías o eran 'nan'
    df_emp = df_emp[df_emp[col_cc] != '']
    df_emp = df_emp[df_emp[col_cc] != 'nan']

    # 4. Filtro numérico final de seguridad
    df_emp = df_emp[df_emp[col_cc].str.isnumeric()]
    
    print(f"✅ Filas válidas para guardar: {len(df_emp)}")

    with transaction.atomic():
        count = 0
        for _, row in df_emp.iterrows():
            # Usamos col_nombre y col_cargo detectados arriba
            valor_nombre = row[col_nombre] if col_nombre else "Sin Nombre"
            valor_cargo = row[col_cargo] if col_cargo else "Sin Cargo"
            
            Empleado.objects.update_or_create(
                cedula=str(row[col_cc]),
                defaults={
                    "nombre_completo": str(valor_nombre).strip(),
                    "cargo": str(valor_cargo).strip(),
                }
            )
            count += 1
        
    os.remove(tmp_path)

    print(f"✅ {count} empleados sincronizados correctamente")
    return f"{count} empleados sincronizados"
"""
EJECUCIÓN:
python manage.py shell
from personal.scheduler import scheduled_fetch
scheduled_fetch()
"""
