import hmac
import logging
import os
import traceback

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required, login_required
from django.contrib import admin
from core.limites import intentos, anotar, limpiar
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect,HttpResponse
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse_lazy
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.http import JsonResponse
from django.apps import apps
from django.contrib.auth.views import ( PasswordResetView, PasswordResetConfirmView)
from django.db.models import Q, CharField, TextField
from usuario.forms import CustomPasswordResetForm
from django.conf import settings
from django.db import close_old_connections
from personal.google_drive_utils import fetch_and_store_empleados
from medicion_rendimiento.tasks import alerta_recordatorio_usuario, alerta_incumplimiento_control


logger = logging.getLogger(__name__)

# Límite de intentos de inicio de sesión: INTENTOS_LOGIN fallos seguidos con el mismo correo bloquean ese correo BLOQUEO_LOGIN segundos
INTENTOS_LOGIN = 5
BLOQUEO_LOGIN = 15 * 60


# Campos de cada app por los que se puede buscar
CAMPOS_BUSQUEDA = {
    'usuario': ('nombre_completo', 'cargo'),
    'personal': ('nombre_completo', 'cargo'),
}


# Límite del panel de administración (el de Django no trae ninguno): por usuario y en total. Y de la recuperación de
# contraseña: por correo y en total. Se cuentan todas las peticiones, existan o no las cuentas, para no revelar cuáles existen.
INTENTOS_ADMIN = 5
INTENTOS_ADMIN_TOTAL = 30
RECUPERACIONES_POR_CORREO = 3
RECUPERACIONES_TOTAL = 100
VENTANA_RECUPERACION = 60 * 60

# Quién puede buscar qué: solo se busca en lo que el usuario ya puede ver
PERMISO_BUSQUEDA = {
    'usuario': ('usuario', 'usuario'),
    'personal': ('personal', 'personal'),
}


def _clave_intentos(correo):
    return f"login-fallos:{correo.lower()}"


def buscar(request):
    """Buscador universal: busca en todas las apps registradas (Usuario, Empleado, etc.)"""
    query = request.GET.get('q', '').strip().lower()
    resultados = []

    if not query:
        return JsonResponse({'resultados': []})

    # Define los modelos a incluir en la búsqueda
    modelos = [
        ('usuario', 'Usuario'),
        ('personal', 'Empleado'),
        ('medicion_por_cuadrilla', 'Cuadrilla'),
    ]

    for app_label, model_name in modelos:
        permiso = PERMISO_BUSQUEDA.get(app_label)
        if permiso is None or not request.user.tiene_permiso(*permiso, 'ver'):
            continue
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            continue

        # Solo nombre y cargo: nunca cédula, correo ni salario
        campos_texto = [c for c in CAMPOS_BUSQUEDA.get(app_label, ()) if any(f.name == c for f in model._meta.fields)]

        if not campos_texto:
            continue

        q_obj = Q()
        for campo in campos_texto:
            q_obj |= Q(**{f"{campo}__icontains": query})

        resultados_modelo = model.objects.filter(q_obj)[:5]  # limitar resultados
        for obj in resultados_modelo:
            resultados.append({
                'app': app_label,
                'modelo': model_name,
                'texto': str(obj),
                'id': getattr(obj, 'id', getattr(obj, 'pk', None)),
            })

    return JsonResponse({'resultados': resultados})


@login_not_required
def login(request):
    """Vista para el inicio de sesión de usuarios"""
    if request.user.is_authenticated:
        return redirect('home')  # Si ya está logueado, lo mandamos a home

    if request.method == 'POST':
        correo = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()
        clave = _clave_intentos(correo)

        if intentos(clave) >= INTENTOS_LOGIN:
            messages.error(request, "Demasiados intentos fallidos. Inténtalo de nuevo en 15 minutos.")
            return render(request, 'core/login.html', status=429)

        user = authenticate(request, username=correo, password=password) if correo and password else None

        if user is not None:
            limpiar(clave)
            auth_login(request, user)
            return redirect('home')

        anotar(clave, BLOQUEO_LOGIN)
        messages.error(request, "Correo o contraseña incorrectos. Inténtalo de nuevo.")

    return render(request, 'core/login.html')


@login_not_required
def login_admin_limitado(request, extra_context=None):
    """Login del panel de administración con límite de intentos: tras INTENTOS_ADMIN fallos de un usuario (o INTENTOS_ADMIN_TOTAL
    entre todos) se bloquea durante BLOQUEO_LOGIN segundos. El de Django no limita nada y es el blanco típico de fuerza bruta."""
    if request.method == 'POST':
        usuario = (request.POST.get('username') or '').strip().lower()
        clave_usuario, clave_total = f"admin-fallos:{usuario}", "admin-fallos:total"
        if intentos(clave_usuario) >= INTENTOS_ADMIN or intentos(clave_total) >= INTENTOS_ADMIN_TOTAL:
            return HttpResponse("Demasiados intentos fallidos. Inténtalo de nuevo en 15 minutos.", status=429)
        respuesta = admin.site.login(request, extra_context)
        if respuesta.status_code == 200:          # el formulario volvió con errores: contraseña incorrecta
            anotar(clave_usuario, BLOQUEO_LOGIN)
            anotar(clave_total, BLOQUEO_LOGIN)
        else:                                     # entró: se redirige
            limpiar(clave_usuario)
        return respuesta
    return admin.site.login(request, extra_context)


@login_not_required
def restablecer_contraseña(request):
    return render(request, 'core/restablecer_contraseña.html')

@login_required(login_url='login')
def home(request):
    return render(request, 'core/home.html')

@login_required
def logout_view(request):
    logout(request)
    list(messages.get_messages(request))  # ← limpia los mensajes
    return redirect('login') 

@property
def email(self):
    return self.correo

@method_decorator(login_not_required, name="dispatch")
class PasswordResetNoRedirectView(PasswordResetView):
    template_name = "core/restablecer_contraseña.html"
    email_template_name = "core/password_reset_email.html"
    subject_template_name = "core/password_reset_subject.txt"
    form_class = CustomPasswordResetForm

    def get_success_url(self):
        return reverse_lazy("password_reset") + "?sent=1"

    def form_valid(self, form):
        correo = form.cleaned_data.get("email")

        # Límite: tras RECUPERACIONES_POR_CORREO pedidos por hora para un correo (o RECUPERACIONES_TOTAL en total) ya no se
        # envía nada, pero la respuesta es la misma de siempre: así no se revela qué correos existen ni se puede usar para
        # llenar de mensajes una bandeja.
        clave_correo = f"recuperar:{correo.lower()}"
        if intentos(clave_correo) >= RECUPERACIONES_POR_CORREO or intentos("recuperar:total") >= RECUPERACIONES_TOTAL:
            logger.warning("Recuperación de contraseña limitada para un correo (demasiados pedidos).")
            return HttpResponseRedirect(self.get_success_url())
        anotar(clave_correo, VENTANA_RECUPERACION)
        anotar("recuperar:total", VENTANA_RECUPERACION)

        for user in form.get_users(correo):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            domain = self.request.get_host()

            context = {
                "user": user,
                "correo": correo,
                "uid": uid,
                "token": token,
                "domain": domain,
                "protocol": "https" if self.request.is_secure() else "http",
            }


            subject = render_to_string(self.subject_template_name, context).strip()
            html_message = render_to_string(self.email_template_name, context)
            text_message = strip_tags(html_message)

            msg = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [correo])
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
        # Evita llamar a super().form_valid(form) para que no se envíe el correo duplicado
        return HttpResponseRedirect(self.get_success_url())

@method_decorator(login_not_required, name="dispatch")
class PasswordResetConfirmNoRedirectView(PasswordResetConfirmView):
    template_name = "core/password_reset_confirm.html"
    def form_valid(self, form):
        # 1) Cambia la contraseña:
        form.save()

        # 2) Prepara contexto con la bandera
        context = self.get_context_data(**self.kwargs)
        context["ok"] = True                     # ← tu JS lo usará

        return render(self.request, self.template_name, context)

@login_not_required
def ejecutar_tareas_cron(request, nombre_tarea):
    # Candado de seguridad: solo quien tenga el token puede ejecutar esto.
    # Sin CRON_SECRET_TOKEN configurado el endpoint queda cerrado (no hay clave por defecto).
    token_secreto = os.environ.get('CRON_SECRET_TOKEN', '')
    token_recibido = request.GET.get('token', '')

    if not token_secreto or not hmac.compare_digest(token_recibido.encode(), token_secreto.encode()):
        return HttpResponse("No autorizado 🛑", status=401)

    # Limpiamos conexiones viejas a la base de datos
    close_old_connections()

    try:
        if nombre_tarea == 'recordatorio':
            alerta_recordatorio_usuario()
            return HttpResponse("✅ Alerta de recordatorio ejecutada")
            
        elif nombre_tarea == 'control':
            alerta_incumplimiento_control()
            return HttpResponse("✅ Alerta de control ejecutada")
            
        elif nombre_tarea == 'drive':
            # Ejecutamos tu función con el ID de la carpeta de Google Drive
            resultado = fetch_and_store_empleados("1aN_dq95lckVrCo6NWMMqjRinV3XTkOCP")
            return HttpResponse(f"✅ Sincronización Drive completada: {resultado}")
            
        else:
            return HttpResponse("Tarea no existe", status=404)
            
    except Exception:
        logger.exception("Falló la tarea programada %s", nombre_tarea)
        return HttpResponse(f"❌ Error ejecutando {nombre_tarea}", status=500)