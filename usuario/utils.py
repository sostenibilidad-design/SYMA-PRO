from functools import wraps
from .models import PermisoUsuario, Funcionalidad

ASIGNAR_KEYS = {"registrar", "crear", "registrar_usuario", "crear_usuario", "add", "create"}

def sincronizar_permisos_usuario(usuario):
    """
    Sincroniza la tabla PermisoUsuario según los permisos del usuario.
    Se puede llamar directamente después de registrar o actualizar.
    """
    if not usuario:
        print("⚠️ No se recibió un usuario válido.")
        return

    # Si el usuario no tiene permisos, limpiamos sus registros previos
    if not usuario.permisos:
        eliminados = PermisoUsuario.objects.filter(usuario=usuario).delete()
        print(f"🧹 Usuario sin permisos: se eliminaron {eliminados[0]} registros de PermisoUsuario.")
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

    print(f"✅ Sincronizados permisos para {usuario.correo} ({len(permisos_json)} apps).")


def eliminar_permisos_usuario(usuario):
    """
    Elimina todos los permisos asociados a un usuario.
    """
    if usuario:
        eliminados = PermisoUsuario.objects.filter(usuario=usuario).delete()
        print(f"🗑️ Eliminados {eliminados[0]} permisos para {usuario.correo}.")


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
            print(f"⚠️ Error en decorador_sync_permisos: {e}")
        return response
    return wrapper
