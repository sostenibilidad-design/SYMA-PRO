from django.urls import path
from proyectos import views

urlpatterns = [
    path('proyectos/', views.proyectos, name='proyectos'),
    path('formulario-proyectos/', views.formulario_proyectos, name='formulario_proyectos'),
    path('eliminar-proyecto/<int:id_proyecto>/', views.eliminar_proyecto, name='eliminar_proyecto'),
]