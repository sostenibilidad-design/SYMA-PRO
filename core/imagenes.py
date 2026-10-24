import base64
import binascii
import io

from django.core.files.base import ContentFile
from PIL import Image

FORMATOS_PERMITIDOS = {'PNG': 'png', 'JPEG': 'jpg', 'WEBP': 'webp'}
MAX_BYTES = 10 * 1024 * 1024


def formato_de_imagen(archivo):
    """Comprueba con Pillow que `archivo` es de verdad una imagen PNG, JPEG o WEBP de hasta 10 MB.

    No se confía en el nombre, la extensión ni el tipo que declara el navegador (un SVG o un HTML disfrazado
    de imagen sería código ejecutable al abrirlo desde el almacenamiento). Devuelve la extensión; si algo falla, ValueError.
    """
    if archivo.size > MAX_BYTES:
        raise ValueError('La imagen pesa más de 10 MB.')
    try:
        archivo.seek(0)
        with Image.open(archivo) as imagen:
            formato = imagen.format
            imagen.verify()
    except Exception:
        raise ValueError('El archivo no es una imagen válida.')
    finally:
        archivo.seek(0)
    if formato not in FORMATOS_PERMITIDOS:
        raise ValueError('Solo se permiten imágenes PNG, JPG o WEBP.')
    return FORMATOS_PERMITIDOS[formato]


def imagen_desde_base64(data_url, nombre):
    """Convierte una firma dibujada («data:image/png;base64,...») en un archivo validado, con la extensión real de la imagen."""
    try:
        _, datos = data_url.split(';base64,', 1)
        contenido = base64.b64decode(datos, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError('La firma no tiene un formato válido.')
    extension = formato_de_imagen(ContentFile(contenido, name=nombre))
    return ContentFile(contenido, name=f'{nombre}.{extension}')
