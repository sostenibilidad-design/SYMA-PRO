from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


def permiso_requerido(app, subarea, accion, json=False):
    """Exige iniciar sesión y tener `accion` en `app`/`subarea` (los superusuarios siempre pasan).

    Sin permiso responde 403: con `json=True` como JSON ({'success': False, 'error': ...}, para las vistas que llama el
    JavaScript con fetch) y si no, con la página de error 403 de Django.
    """
    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(request, *args, **kwargs):
            if not request.user.tiene_permiso(app, subarea, accion):
                if json:
                    return JsonResponse({'success': False, 'ok': False, 'error': 'No tienes permiso para esta acción.'}, status=403)
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
