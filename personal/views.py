from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required #permission_required
from .google_drive_utils import fetch_and_store_empleados

from .models import Empleado
from .forms import Personalform

@login_required
def personal(request):
    empleados = Empleado.objects.all().order_by('nombre_completo')
    # cantidad de filas vacías para mantener formato en tabla
    cantidad_filas_vacias = max (0, 20 - empleados.count())

    #contexto de los datos que se utilizan para filtrar o buscar en la barra
    contexto = {
        "empleados": empleados,
        "filas_vacias": range(cantidad_filas_vacias),
        "app_name": "personal",
    }

    return render(request, 'personal/personal.html', contexto)

# --- NUEVA FUNCIÓN ---
@login_required
#@permission_required('personal.add_empleado', raise_exception=True) # Opcional: seguridad
def sincronizar_personal(request):
    if request.method == 'POST':
        try:
            # ID de la carpeta raíz (Tomado de tu scheduler.py)
            FOLDER_ID = "1aN_dq95lckVrCo6NWMMqjRinV3XTkOCP"
            
            # Ejecutamos la sincronización
            resultado = fetch_and_store_empleados(FOLDER_ID)
            
            messages.success(request, f"Sincronización exitosa: {resultado}")
        except Exception as e:
            messages.error(request, f"Error al extraer datos de Drive: {str(e)}")
            
    return redirect('personal') 