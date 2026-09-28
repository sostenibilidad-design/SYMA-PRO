import gc
from celery import shared_task
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from weasyprint import HTML
from .models import ExportacionBitacora, Bitacora
from django.utils.text import slugify

@shared_task(bind=True)
def generar_pdf_bitacora_async(self, exportacion_id, base_url):
    # 1. Obtenemos el registro y marcamos que empezamos
    exportacion = ExportacionBitacora.objects.get(id=exportacion_id)
    exportacion.estado = 'PROCESANDO'
    exportacion.task_id = self.request.id
    exportacion.save()

    try:
        # 2. Consultamos los datos
        bitacoras = Bitacora.objects.filter(proyecto=exportacion.proyecto).order_by('creado_en')
        context = {'proyecto': exportacion.proyecto, 'bitacoras': bitacoras}
        
        # 3. Renderizamos y generamos PDF en memoria
        html_string = render_to_string('bitacora/imprimir_completa.html', context)
        pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()
        
        # 4. Guardamos el archivo en Google Cloud Storage (o en local si estás en desarrollo)
        nombre_archivo = f'Bitacora_Completa_{slugify(exportacion.proyecto.nombre)}.pdf'
        exportacion.archivo.save(nombre_archivo, ContentFile(pdf_bytes))
        
        # 5. Marcamos como terminado
        exportacion.estado = 'COMPLETADO'
        exportacion.save()
        
    except Exception as e:
        exportacion.estado = 'ERROR'
        exportacion.mensaje_error = str(e)
        exportacion.save()
    finally:
        # 6. Liberamos la memoria de WeasyPrint
        gc.collect()