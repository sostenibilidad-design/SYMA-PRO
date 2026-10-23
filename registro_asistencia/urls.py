from django.urls import path
from registro_asistencia import views, fecha_ingreso

urlpatterns = [
    path('', views.selector_asistencia, name='selector_asistencia'),
    
    # Navegación por niveles: Proyecto > Año > Mes > Quincena > Día (tabla de registros)
    path('proyecto/<int:id_proyecto>/', views.registro_niveles, name='registro_anios'),
    path('proyecto/<int:id_proyecto>/<int:anio>/', views.registro_niveles, name='registro_meses'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/', views.registro_niveles, name='registro_quincenas'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/', views.registro_niveles, name='registro_dias'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/<int:dia>/', views.registro_asistencia, name='registro_asistencia'),
    path('proyecto/<int:id_proyecto>/registro/<int:id_registro>/actualizar/', views.actualizar_registro, name='actualizar_registro'),
    path('proyecto/<int:id_proyecto>/eliminar-dias/', views.eliminar_dias, name='eliminar_dias'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/informe/', views.informe_quincenal, name='informe_quincenal'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/informe/validar/', views.informe_quincenal_validar, name='informe_quincenal_validar'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/informe/excel/', views.descargar_informe_excel, name='descargar_informe_excel'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/informe/fecha-ingreso/<str:cedula>/', fecha_ingreso.fecha_ingreso, name='fecha_ingreso'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/informe/fecha-ingreso/<str:cedula>/revisar/', fecha_ingreso.fecha_ingreso_revisar, name='fecha_ingreso_revisar'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/informe/fecha-ingreso/<str:cedula>/comidas/', fecha_ingreso.fecha_ingreso_comidas, name='fecha_ingreso_comidas'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/informe/fecha-ingreso/<str:cedula>/agregar/', fecha_ingreso.fecha_ingreso_agregar, name='fecha_ingreso_agregar'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/informe/fecha-ingreso/<str:cedula>/eliminar/', fecha_ingreso.fecha_ingreso_eliminar, name='fecha_ingreso_eliminar'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/resumen-actividades/', views.resumen_actividades, name='resumen_actividades'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/resumen-actividades/validar/', views.resumen_actividades_validar, name='resumen_actividades_validar'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/resumen-actividades/excel/', views.descargar_resumen_excel, name='descargar_resumen_excel'),
    path('proyecto/<int:id_proyecto>/<int:anio>/<int:mes>/<int:quincena>/excel/', views.descargar_dias_excel, name='descargar_dias_excel'),
    path('proyecto/<int:id_proyecto>/sincronizar-drive/', views.sincronizar_drive_inicial, name='sincronizar_drive_inicial'),
    path('proyecto/<int:id_proyecto>/paso-1-novedades/', views.paso_1_novedades, name='paso_1_novedades'),
    path('proyecto/<int:id_proyecto>/paso-2-hora-inicio/', views.paso_2_hora_inicio, name='paso_2_hora_inicio'),
    path('proyecto/<int:id_proyecto>/paso-3-hora-salida/', views.paso_3_hora_salida, name='paso_3_hora_salida'),
    path('proyecto/<int:id_proyecto>/paso-4-actividades/', views.paso_4_actividades, name='paso_4_actividades'),
    path('proyecto/<int:id_proyecto>/herramienta/<slug:herramienta>/', views.herramienta_opcional, name='herramienta_opcional'),
    path('proyecto/<int:id_proyecto>/paso-5-vista-previa/', views.paso_5_vista_previa, name='paso_5_vista_previa'),
]