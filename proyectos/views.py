from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Proyecto
from .forms import ProyectoForm
from usuario.decoradores import permiso_requerido

@permiso_requerido('proyectos', 'proyectos', 'ver')
def proyectos(request):
    # Traemos todos los proyectos, los más recientes primero
    lista_proyectos = Proyecto.objects.all().order_by('-id_proyectos')
    return render(request, 'proyectos/proyectos.html', {'proyectos': lista_proyectos})

@permiso_requerido('proyectos', 'proyectos', 'registrar')
def formulario_proyectos(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            messages.success(request, "Proyecto creado exitosamente.")
            return redirect('proyectos')
        
        else:
            messages.error(request, "Por favor revisa los datos del formulario.")
            return render(request, 'proyectos/formulario_proyectos.html', {'form': form})
    else:
        form = ProyectoForm()
    
    return render(request, 'proyectos/formulario_proyectos.html', {'form': form})

@permiso_requerido('proyectos', 'proyectos', 'eliminar')
@require_POST
def eliminar_proyecto(request, id_proyecto):
    proyecto = get_object_or_404(Proyecto, id_proyectos=id_proyecto)
    proyecto.delete()
    messages.success(request, "Proyecto eliminado correctamente.")
    return redirect('proyectos')