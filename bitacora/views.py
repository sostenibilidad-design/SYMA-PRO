import base64
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from proyectos.models import Proyecto
from .models import Bitacora, BitacoraFoto
from django.core.files.base import ContentFile
from usuario.models import Usuario


def selector_bitacora(request):
    proyectos = Proyecto.objects.all()
    context = {
        'proyectos': proyectos,
        'url_destino': 'detalle_bitacora',
    }
    return render(request, 'bitacora/selector_bitacora.html', context)

def detalle_bitacora(request, id_proyecto, id_bitacora=None):
    proyecto = get_object_or_404(Proyecto, id_proyectos=id_proyecto)
    
    bitacoras = Bitacora.objects.filter(proyecto=proyecto).order_by('creado_en')
    total_paginas = bitacoras.count()
    
    primer_id = bitacoras.first().id_bitacora if bitacoras.exists() else None
    ultimo_id = bitacoras.last().id_bitacora if bitacoras.exists() else None

    id_anterior = None
    id_siguiente = None

    if id_bitacora:
        bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora, proyecto=proyecto)
        ids_lista = list(bitacoras.values_list('id_bitacora', flat=True))
        numero_registro = ids_lista.index(bitacora.id_bitacora) + 1
        
        current_index = ids_lista.index(bitacora.id_bitacora)
        if current_index > 0:
            id_anterior = ids_lista[current_index - 1]
        if current_index < len(ids_lista) - 1:
            id_siguiente = ids_lista[current_index + 1]
    else:
        bitacora = None
        numero_registro = total_paginas + 1
        id_anterior = ultimo_id 

    pg_izq = (numero_registro * 2) - 1
    pg_der = numero_registro * 2

    context = {
        'proyecto': proyecto,
        'bitacora': bitacora,
        'pagina_izq': f"{pg_izq:02d}", 
        'pagina_der': f"{pg_der:02d}",
        'primer_id': primer_id,
        'ultimo_id': ultimo_id,
        'id_anterior': id_anterior,
        'id_siguiente': id_siguiente,
    }
    return render(request, 'bitacora/cuaderno_bitacora.html', context)


# --- MOTOR DE AUTO-GUARDADO (AJAX) ---
def autosave_bitacora(request, id_proyecto):
    if request.method == 'POST':
        proyecto = get_object_or_404(Proyecto, id_proyectos=id_proyecto)
        id_bitacora = request.POST.get('id_bitacora')

        # Si no hay ID, es una entrada nueva, la creamos
        if not id_bitacora:
            bitacora = Bitacora.objects.create(proyecto=proyecto)
        else:
            bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora)

        # Actualizamos solo los campos que vengan en el formulario
        if 'fecha' in request.POST: bitacora.fecha = request.POST.get('fecha') or None
        if 'clima_manana' in request.POST: bitacora.clima_manana = request.POST.get('clima_manana')
        if 'clima_tarde' in request.POST: bitacora.clima_tarde = request.POST.get('clima_tarde')
        if 'equipo' in request.POST: bitacora.equipo_obra = request.POST.get('equipo')
        if 'actividades' in request.POST: bitacora.actividades = request.POST.get('actividades')
        if 'cant_maestros' in request.POST: bitacora.cant_maestros = int(request.POST.get('cant_maestros') or 0)
        if 'cant_oficiales' in request.POST: bitacora.cant_oficiales = int(request.POST.get('cant_oficiales') or 0)
        if 'cant_ayudantes' in request.POST: bitacora.cant_ayudantes = int(request.POST.get('cant_ayudantes') or 0)
        if 'cant_contratistas' in request.POST: bitacora.cant_contratistas = int(request.POST.get('cant_contratistas') or 0)
        
        bitacora.save()

        # Devolvemos el ID de la bitácora para que el Frontend lo sepa y siga actualizando el mismo registro
        return JsonResponse({'status': 'success', 'id_bitacora': bitacora.id_bitacora})

def upload_fotos_bitacora(request, id_bitacora):
    if request.method == 'POST':
        bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora)
        archivos = request.FILES.getlist('fotos')
        fotos_guardadas = []
        
        for archivo in archivos:
            foto = BitacoraFoto.objects.create(bitacora=bitacora, url_imagen=archivo)
            fotos_guardadas.append({'id': foto.id_bitacora_fotos, 'url': foto.url_imagen.url})
            
        return JsonResponse({'status': 'success', 'fotos': fotos_guardadas})
    return JsonResponse({'status': 'error'}, status=400)

def delete_foto_bitacora(request, id_foto):
    if request.method == 'POST':
        foto = get_object_or_404(BitacoraFoto, id_bitacora_fotos=id_foto)
        foto.url_imagen.delete() 
        foto.delete() 
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def imprimir_bitacora_hoja(request, id_proyecto, id_bitacora):
    proyecto = get_object_or_404(Proyecto, id_proyectos=id_proyecto)
    
    # Traemos solo el registro exacto en el que el usuario está parado
    bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora, proyecto=proyecto)
    
    context = {
        'proyecto': proyecto,
        'bitacora': bitacora,
    }
    return render(request, 'bitacora/imprimir_hoja.html', context)

def imprimir_bitacora_completa(request, id_proyecto):
    proyecto = get_object_or_404(Proyecto, id_proyectos=id_proyecto)
    
    # Traemos todos los registros del proyecto ordenados desde el más antiguo al más reciente
    bitacoras = Bitacora.objects.filter(proyecto=proyecto).order_by('creado_en')
    
    context = {
        'proyecto': proyecto,
        'bitacoras': bitacoras,
    }
    return render(request, 'bitacora/imprimir_completa.html', context)

def guardar_firmas_bitacora(request, id_proyecto):
    if request.method == 'POST':
        id_bitacora = request.POST.get('id_bitacora_firma')
        if not id_bitacora:
            return JsonResponse({'status': 'error', 'message': 'ID de bitácora no encontrado.'})

        bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora)

        # --- GUARDAR AUTOR ---
        cedula_autor = request.POST.get('cedula_autor')
        if cedula_autor:
            usuario_autor = Usuario.objects.filter(cedula=cedula_autor).first()
            if usuario_autor:
                bitacora.autor = usuario_autor

        firma_file_autor = request.FILES.get('firma_archivo_autor')
        firma_base64_autor = request.POST.get('firma_dibujada_autor')

        if firma_file_autor:
            bitacora.firma_autor_url = firma_file_autor
        elif firma_base64_autor and 'data:image' in firma_base64_autor:
            format, imgstr = firma_base64_autor.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'firma_autor_{bitacora.id_bitacora}.{ext}')
            bitacora.firma_autor_url = data

        # --- GUARDAR SUPERVISOR ---
        cedula_supervisor = request.POST.get('cedula_supervisor')
        if cedula_supervisor:
            usuario_supervisor = Usuario.objects.filter(cedula=cedula_supervisor).first()
            if usuario_supervisor:
                bitacora.supervisor = usuario_supervisor

        firma_file_sup = request.FILES.get('firma_archivo_supervisor')
        firma_base64_sup = request.POST.get('firma_dibujada_supervisor')

        if firma_file_sup:
            bitacora.firma_supervisor_url = firma_file_sup
        elif firma_base64_sup and 'data:image' in firma_base64_sup:
            format, imgstr = firma_base64_sup.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'firma_sup_{bitacora.id_bitacora}.{ext}')
            bitacora.firma_supervisor_url = data

        bitacora.save()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)