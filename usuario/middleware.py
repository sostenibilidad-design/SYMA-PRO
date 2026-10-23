from django.shortcuts import redirect
from django.urls import reverse


class CambioPasswordObligatorioMiddleware:
    """Quien tenga `debe_cambiar_password` solo puede ver el inicio (donde está el formulario de cambio),
    enviar el cambio y cerrar sesión; cualquier otra página lo devuelve al inicio hasta que cambie la contraseña."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and getattr(user, 'debe_cambiar_password', False):
            permitidas = {reverse('home'), reverse('cambiar_password'), reverse('logout')}
            if request.path not in permitidas and not request.path.startswith(('/static/', '/media/')):
                return redirect('home')
        return self.get_response(request)
