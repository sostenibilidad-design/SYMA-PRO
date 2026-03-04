from django.urls import path
from entrada_y_salida_del_personal import views

urlpatterns = [
    path('entrada-salida-personal/', views.entrada_salida_personal, name='entrada_salida_personal'),
]