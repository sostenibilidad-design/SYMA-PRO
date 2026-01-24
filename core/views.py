from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
import traceback


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
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            continue

        campos_texto = [
            f.name for f in model._meta.fields
            if f.get_internal_type() in ('CharField', 'TextField', 'EmailField')
        ]

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


def login(request):
    """Vista para el inicio de sesión de usuarios"""
    if request.user.is_authenticated:
        return redirect('home')  # Si ya está logueado, lo mandamos a home

    if request.method == 'POST':
        correo = request.POST.get('username').strip()
        password = request.POST.get('password').strip()

        user = authenticate(request, username=correo, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('home')

        messages.error(request, "Correo o contraseña incorrectos. Inténtalo de nuevo.")

    return render(request, 'core/login.html')


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

class PasswordResetNoRedirectView(PasswordResetView):
    template_name = "core/restablecer_contraseña.html"
    email_template_name = "core/password_reset_email.html"
    subject_template_name = "core/password_reset_subject.txt"
    form_class = CustomPasswordResetForm

    def get_success_url(self):
        return reverse_lazy("password_reset") + "?sent=1"

    def form_valid(self, form):
        correo = form.cleaned_data.get("email")


        for user in form.get_users(correo):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            domain = get_current_site(self.request).domain

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

class PasswordResetConfirmNoRedirectView(PasswordResetConfirmView):
    template_name = "core/password_reset_confirm.html"
    def form_valid(self, form):
        # 1) Cambia la contraseña:
        form.save()

        # 2) Prepara contexto con la bandera
        context = self.get_context_data(**self.kwargs)
        context["ok"] = True                     # ← tu JS lo usará

        return render(self.request, self.template_name, context)



