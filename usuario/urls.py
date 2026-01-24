from django.contrib.auth import views as auth_views
from django.urls import path
from usuario import views

urlpatterns = [
    path('usuario/', views.usuario, name='usuario'),
    path('registrar_usuario/', views.registrar_usuario, name='registrar_usuario'),
    path('actualizar/<int:pk>/', views.actualizar_usuario, name='actualizar'),
    path('cambiar_password/', views.cambiar_password, name='cambiar_password'),
]