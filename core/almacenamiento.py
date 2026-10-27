import hashlib

from django.core.cache import caches
from storages.backends.gcloud import GoogleCloudStorage

# Margen para no entregar una URL a punto de vencer: se guarda 10 minutos menos de lo que dura la firma
MARGEN_VENCIMIENTO = 10 * 60


class GoogleCloudStorageConCache(GoogleCloudStorage):
    """Igual que GoogleCloudStorage, pero guarda en memoria la URL firmada de cada archivo.

    En Cloud Run cada `.url` firma con la API IAM (signBlob), que es una llamada de red; una tabla con 2 fotos por
    fila hacía cientos de llamadas seguidas antes de responder. La URL firmada sirve hasta GS_EXPIRATION, así que se
    reutiliza mientras le quede margen.

    Usa la caché local `urls_firmadas` (memoria de cada proceso) y no Redis: una página con decenas de fotos haría decenas
    de comandos a Redis por visita, y si Redis falla cada uno sería una espera inútil.
    """

    def url(self, name, parameters=None):
        # Con parámetros extra (por ejemplo una descarga con otro nombre) la URL cambia: se firma cada vez
        if parameters:
            return super().url(name, parameters)

        cache = caches['urls_firmadas']
        clave = 'url_firmada:' + hashlib.sha256(f'{self.bucket_name}/{name}'.encode()).hexdigest()
        url = cache.get(clave)
        if url is None:
            url = super().url(name)
            duracion = int(self.expiration.total_seconds()) - MARGEN_VENCIMIENTO
            if duracion > 0:
                cache.set(clave, url, timeout=duracion)
        return url
