import os
import re
from django.core.management.base import BaseCommand
from django.apps import apps
from usuario.models import Funcionalidad

# 🔧 Ignorar apps y funciones
IGNORAR_APPS = {
    'core',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
}

FUNCIONES_IGNORAR = {
    'render', 'redirect', 'JsonResponse',
    'HttpResponse', 'get_object_or_404',
    'get_list_or_404'
}

PATRONES_IGNORAR = [
    'filtro', 'filtrar', 'registrar', 'detalle', 'form', 'base', 'actualizar',
    'agregar','reporte','cambiar_password','correo_bienvenida','obtener_cumplimiento'
]

PALABRAS_CLAVE = ["registrar", "eliminar", "actualizar", "descarga", "reporte", "rendimiento", "drive" ]


class Command(BaseCommand):
    help = "Escanea las apps, subáreas y funcionalidades (vistas y plantillas HTML)"

    def handle(self, *args, **options):
        print("🔍 Iniciando escaneo de funcionalidades...\n")

        total_nuevas = 0
        total_existentes = 0

        for app in apps.get_app_configs():
            if app.name in IGNORAR_APPS:
                continue

            print(f"📁 Analizando área: {app.label}")

            app_path = app.path
            vistas = self.scan_views(app_path)
            plantillas = self.scan_templates(app_path)

            print(f"   🧩 Encontradas {len(vistas)} vistas y {len(plantillas)} subáreas")

            # 💾 Guardar vistas
            for vista in vistas:
                obj, creado = Funcionalidad.objects.get_or_create(
                    app=app.label,
                    submodulo=vista,
                    defaults={'acciones': ['ver']}
                )
                if creado:
                    total_nuevas += 1
                else:
                    total_existentes += 1

            # 💾 Guardar plantillas (subáreas y funcionalidades)
            for subarea, acciones in plantillas.items():
                obj, creado = Funcionalidad.objects.get_or_create(
                    app=app.label,
                    submodulo=subarea,
                    defaults={'acciones': acciones}
                )
                if not creado:
                    # Si ya existía, actualizamos las acciones
                    obj.acciones = acciones
                    obj.save()
                    total_existentes += 1
                else:
                    total_nuevas += 1

        # 🧾 Resumen
        print("\n📋 Resumen detallado de funcionalidades encontradas:")
        funcionalidades = Funcionalidad.objects.all().order_by('app', 'submodulo')
        if not funcionalidades.exists():
            print("  ⚠️ No se encontraron funcionalidades registradas.")
        else:
            for f in funcionalidades:
                print(f"  - {f.app} → {f.submodulo} → {', '.join(f.acciones)}")

        print(f"\n🏁 Escaneo completado → {total_nuevas} nuevas funcionalidades detectadas.\n")

    # ------------------------------------------------------------------
    def scan_views(self, app_path):
        """Escanea vistas (views.py y submódulos)"""
        funcionalidades = set()
        views_dir = os.path.join(app_path, "views")

        # Si hay carpeta views/
        if os.path.isdir(views_dir):
            archivos = [
                os.path.join(views_dir, f)
                for f in os.listdir(views_dir)
                if f.endswith(".py")
            ]
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
        """Escanea los archivos HTML para detectar subáreas y acciones"""
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

                acciones = [p for p in PALABRAS_CLAVE if p in contenido]
                if not acciones:
                    acciones = ["ver"]

                subarea = file.replace(".html", "")
                subareas[subarea] = acciones

        return subareas
