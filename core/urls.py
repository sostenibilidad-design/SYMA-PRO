from django.contrib.auth import views as auth_views
from django.urls import path
from core.views import PasswordResetNoRedirectView, PasswordResetConfirmNoRedirectView

from core import views

urlpatterns = [
    path('buscar/', views.buscar, name='buscar'),
    path('', views.login, name='login'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),

    # Si solo quieres mostrar una página informativa, mantenla
    path('restablecer_contraseña/', views.restablecer_contraseña, name='restablecer_contraseña'),

# --------------------- Recuperar contraseña  ------------------------------

    path("password_reset/",PasswordResetNoRedirectView.as_view(), name="password_reset"),

    path("reset/<uidb64>/<token>/", PasswordResetConfirmNoRedirectView.as_view(), name="password_reset_confirm"),
]
