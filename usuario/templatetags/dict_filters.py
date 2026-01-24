from django import template
from usuario.models import PermisoUsuario

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un valor de diccionario de manera segura."""
    if dictionary is None:
        return []
    return dictionary.get(key, []) 

@register.filter
def split(value, delimiter=','):
    """Divide un string por el delimitador dado y devuelve una lista."""
    if value:
        return [v.strip() for v in value.split(delimiter)]
    return []

@register.filter
def has_perm(user, value):
    if not user or not getattr(user, "id", None):
        return False

    try:
        partes = [v.strip().lower() for v in value.split(",")]
        if len(partes) < 3:
            return False

        app, sub, accion = partes

        permiso = PermisoUsuario.objects.filter(
            usuario=user,
            funcionalidad__app=app,
            funcionalidad__submodulo=sub
        ).first()

        if not permiso:
            return False

        acciones = [a.lower() for a in (permiso.acciones_permitidas or [])]
        return accion.lower() in acciones

    except Exception as e:
        return False
