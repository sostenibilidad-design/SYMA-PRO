import os
import re
from django.core.management.base import BaseCommand
from django.apps import apps
from usuario.models import Funcionalidad, PermisoUsuario

# 🔧 Ignorar apps y funciones que no son del negocio
IGNORAR_APPS = {
    'core', 'django.contrib.admin', 'django.contrib.auth',
    'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles',
    'widget_tweaks', 'sites', 'django_apscheduler', 'humanize',
    'storages', 'anymail'
}

FUNCIONES_IGNORAR = {
    'render', 'redirect', 'JsonResponse', 'HttpResponse', 
    'get_object_or_404', 'get_list_or_404'
}

# 🚫 PATRONES IGNORADOS: Aquí bloqueamos todas las vistas secundarias, modales y acciones
PATRONES_IGNORAR = [
    'filtro', 'filtrar', 'form', 'base', 'correo_bienvenida', 
    'modal', 'guardar_configuracion', 'api_', 
    'sincronizar_', 'exportar_', 'imprimir', 'pdf', 'upload_',
    'autosave', 'delete_', 'guardar_firmas', 'selector', 'obtener_',
    'detalle', 'agregar', 'cambiar_password',
    # 🔥 Agregados para eliminar la basura de las imágenes:
    'registrar_', 'reporte_', 'eliminar_', 'actualizar_'
]

# 🔄 Consolidamos palabras similares en acciones principales y limpias
MAPEO_ACCIONES = {
    "registrar": "registrar",
    "crear": "registrar",
    "guardar": "registrar",
    
    "actualizar": "actualizar",
    "editar": "actualizar",
    
    "eliminar": "eliminar",
    "borrar": "eliminar",
    
    "descarga": "descargar",
    "descargar": "descargar",
    "imprimir": "descargar",
    "pdf": "descargar",
    "excel": "descargar",
    
    "reporte": "reporte",
    "rendimiento": "rendimiento",
    "drive": "drive"
}

class Command(BaseCommand):
    help = "Escanea las apps y registra funcionalidades de forma limpia."

    def handle(self, *args, **options):
        print("🧹 Limpiando registros basura por patrones prohibidos...")
        
        # 1. LIMPIEZA DE BASURA POR PATRONES
        for p in PATRONES_IGNORAR:
            basura = Funcionalidad.objects.filter(submodulo__icontains=p)
            for b in basura:
                print(f"   🗑️ Eliminando vista auxiliar ignorada: {b.submodulo}")
                b.delete()

        print("\n🔍 Iniciando escaneo inteligente de funcionalidades...\n")

        total_nuevas = 0
        total_existentes = 0
        
        # 🔥 LISTA MAESTRA PARA RASTREAR LO QUE REALMENTE EXISTE EN EL CÓDIGO
        funcionalidades_validas = set()

        for app in apps.get_app_configs():
            if app.name in IGNORAR_APPS:
                continue

            print(f"📁 Analizando área: {app.label}")

            app_path = app.path
            vistas = self.scan_views(app_path)
            plantillas = self.scan_templates(app_path)

            funcionalidades_finales = {}

            # Agregamos primero las vistas
            for v in vistas:
                funcionalidades_finales[v] = {"ver"}

            # Combinamos con las plantillas descubiertas
            for p, acciones in plantillas.items():
                if p not in funcionalidades_finales:
                    funcionalidades_finales[p] = set()
                funcionalidades_finales[p].update(acciones)
                funcionalidades_finales[p].add("ver") # Toda vista debe tener "ver"

            # Guardamos en la base de datos
            for submodulo, acciones in funcionalidades_finales.items():
                acciones_lista = list(acciones)
                
                obj, creado = Funcionalidad.objects.get_or_create(
                    app=app.label,
                    submodulo=submodulo,
                    defaults={'acciones': acciones_lista}
                )
                
                if not creado:
                    # Sobrescribimos por si se depuraron acciones
                    obj.acciones = acciones_lista
                    obj.save()
                    total_existentes += 1
                else:
                    total_nuevas += 1
                
                # Agregamos a las válidas
                funcionalidades_validas.add((app.label, submodulo))

        # 🔥 2. LIMPIEZA DE HUÉRFANOS (Lo que borraste del código o bloqueaste) 🔥
        print("\n🕵️ Buscando módulos eliminados del código fuente...")
        huerfanas_eliminadas = 0
        for f in Funcionalidad.objects.all():
            if (f.app, f.submodulo) not in funcionalidades_validas:
                print(f"   🧹 Eliminando submódulo huérfano o bloqueado: {f.app} -> {f.submodulo}")
                f.delete()
                huerfanas_eliminadas += 1

        print("\n📋 Resumen detallado de funcionalidades limpias:")
        funcionalidades = Funcionalidad.objects.all().order_by('app', 'submodulo')
        for f in funcionalidades:
            print(f"  - {f.app} → {f.submodulo} → {', '.join(f.acciones)}")

        print(f"\n🏁 Escaneo completado → {total_nuevas} nuevas, {huerfanas_eliminadas} eliminadas.\n")

    # ------------------------------------------------------------------
    def scan_views(self, app_path):
        funcionalidades = set()
        views_dir = os.path.join(app_path, "views")

        if os.path.isdir(views_dir):
            archivos = [os.path.join(views_dir, f) for f in os.listdir(views_dir) if f.endswith(".py")]
        else:
            archivo = os.path.join(app_path, "views.py")
            archivos = [archivo] if os.path.exists(archivo) else []

        for ruta in archivos:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()

            matches = re.findall(r"def (\w+)\s*\(request", contenido)
            for funcion in matches:
                if funcion in FUNCIONES_IGNORAR:
                    continue
                if any(p in funcion.lower() for p in PATRONES_IGNORAR):
                    continue
                
                funcionalidades.add(funcion)

        return funcionalidades

    # ------------------------------------------------------------------
    def scan_templates(self, app_path):
        subareas = {}
        templates_dir = os.path.join(app_path, "templates")

        if not os.path.exists(templates_dir):
            return subareas

        for root, _, files in os.walk(templates_dir):
            for file in files:
                if not file.endswith(".html"):
                    continue
                
                if any(p in file.lower() for p in PATRONES_IGNORAR):
                    continue

                ruta = os.path.join(root, file)
                with open(ruta, "r", encoding="utf-8") as f:
                    contenido = f.read().lower()

                acciones_encontradas = set()
                
                permisos_explicitos = re.findall(r'has_perm:"[^"]+,[^"]+,([^"]+)"', contenido)
                for perm in permisos_explicitos:
                    perm = perm.strip()
                    if perm in MAPEO_ACCIONES.values() or perm == 'ver':
                        acciones_encontradas.add(perm)

                for palabra, accion_canonica in MAPEO_ACCIONES.items():
                    if re.search(rf'\b{palabra}\b', contenido):
                        acciones_encontradas.add(accion_canonica)

                # Regla estricta para evitar falsos positivos de eliminar
                if "eliminar" in acciones_encontradas and "eliminar" not in permisos_explicitos:
                    acciones_encontradas.remove("eliminar")

                subarea = file.replace(".html", "")
                subareas[subarea] = acciones_encontradas

        return subareas