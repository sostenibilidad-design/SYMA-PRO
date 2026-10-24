"""Contadores de intentos con caducidad, para limitar los intentos de inicio de sesión, del panel de administración y de
recuperación de contraseña. Usan la caché de Django: con Redis valen para todas las instancias; con la caché en memoria,
para cada instancia."""
from django.core.cache import cache


def intentos(clave):
    return cache.get(clave, 0) or 0   # con IGNORE_EXCEPTIONS una caída de Redis devuelve None


def anotar(clave, ventana):
    """Suma un intento. La clave caduca `ventana` segundos después del primero (add() fija el plazo; incr() no lo renueva)."""
    cache.add(clave, 0, ventana)
    try:
        cache.incr(clave)
    except ValueError:
        cache.set(clave, 1, ventana)


def limpiar(clave):
    cache.delete(clave)
