from django.contrib.auth import views as auth_views
from django.urls import path
from personal import views

urlpatterns = [
    path('personal/', views.personal, name='personal'),
    path('sincronizar-personal/', views.sincronizar_personal, name='sincronizar_personal'),
]