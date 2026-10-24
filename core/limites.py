"""Contadores de intentos con caducidad, para limitar los intentos de inicio de sesión, del panel de administración y de
recuperación de contraseña. Usan la caché de Django: con Redis valen para todas las instancias; con la caché en memoria,
para cada instancia. Si la caché falla (p. ej. Redis caído) el sitio sigue funcionando y solo se pierde el límite."""
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


def intentos(clave):
    try:
        return cache.get(clave, 0) or 0
    except Exception:
        logger.warning("La caché no responde: no se pudo leer el contador de intentos.", exc_info=True)
        return 0


def anotar(clave, ventana):
    """Suma un intento. La clave caduca `ventana` segundos después del primero (add() fija el plazo; incr() no lo renueva)."""
    try:
        cache.add(clave, 0, ventana)
        try:
            cache.incr(clave)
        except ValueError:
            cache.set(clave, 1, ventana)
    except Exception:
        logger.warning("La caché no responde: no se pudo anotar el intento.", exc_info=True)


def limpiar(clave):
    try:
        cache.delete(clave)
    except Exception:
        logger.warning("La caché no responde: no se pudo limpiar el contador de intentos.", exc_info=True)
