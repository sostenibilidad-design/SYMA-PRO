from django.shortcuts import render
from .models import Empleado
from .forms import Personalform


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
