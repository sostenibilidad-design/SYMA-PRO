from django.contrib.auth import views as auth_views
from django.urls import path
from medicion_rendimiento import views

urlpatterns = [
    # Medición de rendimiento por cuadrilla
    path('actividad_cuadrilla/', views.medicion_por_cuadrilla, name='actividad_cuadrilla'),
    path('reporte_cuadrilla/', views.reporte_cuadrilla, name='reporte_cuadrilla'),
    path('registrar-inicio/', views.registrar_inicio_medicion, name='registrar_inicio_medicion'),
    path('actualizar_cuadrilla/<int:id>/', views.actualizar_cuadrilla, name='actualizar_cuadrilla'),
    path('registrar-fin/<int:id>/', views.registrar_fin_medicion, name='registrar_fin_medicion'),
    path('registrar-cumplimiento/', views.registrar_cumplimiento, name='registrar_cumplimiento'),
    path('obtener-cumplimiento/', views.obtener_cumplimiento, name='obtener_cumplimiento'),
    path("api/demanda-empleados/",views.api_demanda_empleados,name="api_demanda_empleados"),
    # Medición de rendimiento individual
    path('medicion_individual/', views.medicion_individual, name='medicion_individual'),
]