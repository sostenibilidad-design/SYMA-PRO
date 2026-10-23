import base64
from datetime import datetime
import tempfile
import gc
from django.http import FileResponse
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils.text import slugify
from proyectos.models import Proyecto
from .models import Bitacora, BitacoraFoto, ExportacionBitacora
from django.core.files.base import ContentFile
from weasyprint import HTML
from .tasks import generar_pdf_bitacora_async
from usuario.models import Usuario
from usuario.decoradores import permiso_requerido
from core.imagenes import formato_de_imagen, imagen_desde_base64


@permiso_requerido('bitacora', 'cuaderno_bitacora', 'ver')
def selector_bitacora(request):
    proyectos = Proyecto.objects.all()
    context = {
        'proyectos': proyectos,
        'url_destino': 'detalle_bitacora',
    }
    return render(request, 'bitacora/selector_bitacora.html', context)

@permiso_requerido('bitacora', 'cuaderno_bitacora', 'ver')
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


def entero_seguro(texto, maximo=100000):
    """Entero entre 0 y `maximo`; lo que no se pueda leer como número cuenta como 0."""
    try:
        return min(max(int(texto or 0), 0), maximo)
    except (TypeError, ValueError):
        return 0


# --- MOTOR DE AUTO-GUARDADO (AJAX) ---
@permiso_requerido('bitacora', 'cuaderno_bitacora', 'ver', json=True)
def autosave_bitacora(request, id_proyecto):
    if request.method == 'POST':
        proyecto = get_object_or_404(Proyecto, id_proyectos=id_proyecto)
        id_bitacora = request.POST.get('id_bitacora')

        # Si no hay ID, es una entrada nueva, la creamos
        if not id_bitacora:
            bitacora = Bitacora.objects.create(proyecto=proyecto)
        else:
            bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora, proyecto=proyecto)

        # Actualizamos solo los campos que vengan en el formulario
        try:
            if 'fecha' in request.POST:
                bitacora.fecha = datetime.strptime(request.POST['fecha'], '%Y-%m-%d').date() if request.POST['fecha'] else None
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'La fecha no es válida.'}, status=400)
        if 'clima_manana' in request.POST: bitacora.clima_manana = request.POST.get('clima_manana')[:20]
        if 'clima_tarde' in request.POST: bitacora.clima_tarde = request.POST.get('clima_tarde')[:20]
        if 'equipo' in request.POST: bitacora.equipo_obra = request.POST.get('equipo')
        if 'actividades' in request.POST: bitacora.actividades = request.POST.get('actividades')
        if 'cant_maestros' in request.POST: bitacora.cant_maestros = entero_seguro(request.POST.get('cant_maestros'))
        if 'cant_oficiales' in request.POST: bitacora.cant_oficiales = entero_seguro(request.POST.get('cant_oficiales'))
        if 'cant_ayudantes' in request.POST: bitacora.cant_ayudantes = entero_seguro(request.POST.get('cant_ayudantes'))
        if 'cant_contratistas' in request.POST: bitacora.cant_contratistas = entero_seguro(request.POST.get('cant_contratistas'))
        
        bitacora.save()

        # Devolvemos el ID de la bitácora para que el Frontend lo sepa y siga actualizando el mismo registro
        return JsonResponse({'status': 'success', 'id_bitacora': bitacora.id_bitacora})

@permiso_requerido('bitacora', 'cuaderno_bitacora', 'ver', json=True)
def upload_fotos_bitacora(request, id_bitacora):
    if request.method == 'POST':
        bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora)
        archivos = request.FILES.getlist('fotos')
        fotos_guardadas = []
        
        for archivo in archivos:
            try:
                formato_de_imagen(archivo)
            except ValueError as e:
                return JsonResponse({'status': 'error', 'message': f'{archivo.name}: {e}'}, status=400)
        for archivo in archivos:
            foto = BitacoraFoto.objects.create(bitacora=bitacora, url_imagen=archivo)
            fotos_guardadas.append({'id': foto.id_bitacora_fotos, 'url': foto.url_imagen.url})
            
        return JsonResponse({'status': 'success', 'fotos': fotos_guardadas})
    return JsonResponse({'status': 'error'}, status=400)

@permiso_requerido('bitacora', 'cuaderno_bitacora', 'ver', json=True)
def delete_foto_bitacora(request, id_foto):
    if request.method == 'POST':
        foto = get_object_or_404(BitacoraFoto, id_bitacora_fotos=id_foto)
        foto.url_imagen.delete() 
        foto.delete() 
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@permiso_requerido('bitacora', 'cuaderno_bitacora', 'descargar')
def imprimir_bitacora_hoja(request, id_proyecto, id_bitacora):
    proyecto = get_object_or_404(Proyecto, id_proyectos=id_proyecto)
    
    # Traemos solo el registro exacto en el que el usuario está parado
    bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora, proyecto=proyecto)
    
    context = {
        'proyecto': proyecto,
        'bitacora': bitacora,
    }
    return render(request, 'bitacora/imprimir_hoja.html', context)

@permiso_requerido('bitacora', 'cuaderno_bitacora', 'descargar')
def imprimir_bitacora_completa(request, id_proyecto):
    proyecto = get_object_or_404(Proyecto, id_proyectos=id_proyecto)
    
    # 1. Creamos el registro en la BD
    exportacion = ExportacionBitacora.objects.create(proyecto=proyecto)
    
    # 2. Enviamos la tarea a la cola de Redis/Celery
    base_url = request.build_absolute_uri('/')
    generar_pdf_bitacora_async.delay(exportacion.id, base_url)
    
    # 3. Liberamos el servidor web instantáneamente devolviendo el ID
    return JsonResponse({
        'status': 'success', 
        'exportacion_id': exportacion.id, 
        'mensaje': 'Generación iniciada en segundo plano.'
    }, status=202)

@permiso_requerido('bitacora', 'cuaderno_bitacora', 'descargar', json=True)
def consultar_estado_descarga(request, exportacion_id):
    exportacion = get_object_or_404(ExportacionBitacora, id=exportacion_id)
    
    url_archivo = None
    if exportacion.archivo and exportacion.estado == 'COMPLETADO':
        url_archivo = exportacion.archivo.url

    return JsonResponse({
        'estado': exportacion.estado,
        'url_archivo': url_archivo,
        'error': exportacion.mensaje_error
    })

@permiso_requerido('bitacora', 'cuaderno_bitacora', 'ver', json=True)
def guardar_firmas_bitacora(request, id_proyecto):
    if request.method == 'POST':
        id_bitacora = request.POST.get('id_bitacora_firma')
        if not id_bitacora:
            return JsonResponse({'status': 'error', 'message': 'ID de bitácora no encontrado.'})

        bitacora = get_object_or_404(Bitacora, id_bitacora=id_bitacora, proyecto__id_proyectos=id_proyecto)

        # --- GUARDAR AUTOR ---
        cedula_autor = request.POST.get('cedula_autor')
        if cedula_autor:
            usuario_autor = Usuario.objects.filter(cedula=cedula_autor).first()
            if usuario_autor:
                bitacora.autor = usuario_autor

        firma_file_autor = request.FILES.get('firma_archivo_autor')
        firma_base64_autor = request.POST.get('firma_dibujada_autor')

        try:
            if firma_file_autor:
                formato_de_imagen(firma_file_autor)
                bitacora.firma_autor_url = firma_file_autor
            elif firma_base64_autor and 'data:image' in firma_base64_autor:
                bitacora.firma_autor_url = imagen_desde_base64(firma_base64_autor, f'firma_autor_{bitacora.id_bitacora}')
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Firma del autor: {e}'}, status=400)

        # --- GUARDAR SUPERVISOR ---
        cedula_supervisor = request.POST.get('cedula_supervisor')
        if cedula_supervisor:
            usuario_supervisor = Usuario.objects.filter(cedula=cedula_supervisor).first()
            if usuario_supervisor:
                bitacora.supervisor = usuario_supervisor

        firma_file_sup = request.FILES.get('firma_archivo_supervisor')
        firma_base64_sup = request.POST.get('firma_dibujada_supervisor')

        try:
            if firma_file_sup:
                formato_de_imagen(firma_file_sup)
                bitacora.firma_supervisor_url = firma_file_sup
            elif firma_base64_sup and 'data:image' in firma_base64_sup:
                bitacora.firma_supervisor_url = imagen_desde_base64(firma_base64_sup, f'firma_sup_{bitacora.id_bitacora}')
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Firma del supervisor: {e}'}, status=400)

        bitacora.save()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)