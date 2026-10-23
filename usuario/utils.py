import logging
from functools import wraps
from .models import PermisoUsuario, Funcionalidad

logger = logging.getLogger(__name__)

ASIGNAR_KEYS = {"registrar", "crear", "registrar_usuario", "crear_usuario", "add", "create"}

def acciones_del_usuario(usuario):
    """{(app, submódulo): {acciones}} que tiene el usuario, en una sola consulta."""
    return {
        (p.funcionalidad.app, p.funcionalidad.submodulo): set(p.acciones_permitidas or [])
        for p in PermisoUsuario.objects.filter(usuario=usuario).select_related('funcionalidad')
    }


def armar_permisos(quien, tree, post, actuales=None):
    """Estructura de permisos que queda según el formulario de registrar o actualizar un usuario.

    Solo cuentan las acciones que existen para cada funcionalidad. Quien no es superusuario solo puede conceder o quitar las
    acciones que él mismo tiene: las demás se ignoran en el formulario y, al actualizar, se conservan como estaban. Sin esto,
    quien puede registrar o actualizar usuarios podría darse (o dar) cualquier permiso del sistema.
    """
    propias = None if quien.is_superuser else acciones_del_usuario(quien)
    actuales = actuales or {}
    permisos = {}
    for area, subareas in tree.items():
        for sub, acciones in subareas.items():
            conocidas = set(acciones)
            elegidas = set(post.getlist(f"perm__{area}__{sub}")) & conocidas
            if propias is not None:
                mias = propias.get((area, sub), set())
                previas = set(actuales.get(area, {}).get(sub, []))
                elegidas = (elegidas & mias) | (previas - mias)
            elegidas &= conocidas
            if elegidas:
                elegidas.add('ver')        # quien tiene cualquier acción en una pantalla puede verla
                permisos.setdefault(area, {})[sub] = [a for a in acciones if a in elegidas]
    return permisos


def sincronizar_permisos_usuario(usuario):
    """
    Sincroniza la tabla PermisoUsuario según los permisos del usuario.
    Se puede llamar directamente después de registrar o actualizar.
    """
    if not usuario:
        logger.warning("No se recibió un usuario válido para sincronizar permisos.")
        return

    # Si el usuario no tiene permisos, limpiamos sus registros previos
    if not usuario.permisos:
        eliminados = PermisoUsuario.objects.filter(usuario=usuario).delete()
        logger.info("Usuario sin permisos: se eliminaron %s registros de PermisoUsuario.", eliminados[0])
        return

    # Limpia los permisos antiguos
    PermisoUsuario.objects.filter(usuario=usuario).delete()

    permisos_json = usuario.permisos or {}
    for app, submodulos in permisos_json.items():
        for sub, acciones in submodulos.items():
            func = Funcionalidad.objects.filter(app=app, submodulo=sub).first()
            if not func:
                continue
            acciones_lower = {str(a).lower() for a in (acciones or [])}
            puede_asignar_flag = bool(ASIGNAR_KEYS.intersection(acciones_lower))
            PermisoUsuario.objects.create(
                usuario=usuario,
                funcionalidad=func,
                acciones_permitidas=acciones,
                puede_asignar=puede_asignar_flag
            )

    logger.info("Sincronizados permisos del usuario %s (%s apps).", usuario.pk, len(permisos_json))


def eliminar_permisos_usuario(usuario):
    """
    Elimina todos los permisos asociados a un usuario.
    """
    if usuario:
        eliminados = PermisoUsuario.objects.filter(usuario=usuario).delete()
        logger.info("Eliminados %s permisos del usuario %s.", eliminados[0], usuario.pk)


def decorador_sync_permisos(view_func):
    """
    Decorador opcional para ejecutar sincronización automáticamente
    después de guardar/eliminar un usuario desde una vista.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        try:
            from .models import Usuario
            usuario_id = kwargs.get("pk") or request.POST.get("id") or request.GET.get("id")
            if usuario_id:
                usuario = Usuario.objects.filter(id=usuario_id).first()
                if usuario:
                    sincronizar_permisos_usuario(usuario)
        except Exception as e:
            logger.exception("Error en decorador_sync_permisos")
        return response
    return wrapper
