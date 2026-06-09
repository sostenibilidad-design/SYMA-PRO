from django.urls import path
from bitacora import views

urlpatterns = [
    # Selector principal
    path('', views.selector_bitacora, name='bitacora'),
    
    path('proyecto/<int:id_proyecto>/', views.detalle_bitacora, name='detalle_bitacora'),
    
    path('proyecto/<int:id_proyecto>/<int:id_bitacora>/', views.detalle_bitacora, name='detalle_bitacora_id'),

    # Descargar hoja específica
    path('proyecto/<int:id_proyecto>/imprimir/<int:id_bitacora>/', views.imprimir_bitacora_hoja, name='imprimir_bitacora_hoja'),

    # Descargar bitácora completa
    path('proyecto/<int:id_proyecto>/imprimir/', views.imprimir_bitacora_completa, name='imprimir_bitacora_completa'),
    
    # Endpoints de la API (Auto-guardado y Fotos)
    path('api/autosave/<int:id_proyecto>/', views.autosave_bitacora, name='autosave_bitacora'),
    path('api/upload_fotos/<int:id_bitacora>/', views.upload_fotos_bitacora, name='upload_fotos_bitacora'),
    path('api/delete_foto/<int:id_foto>/', views.delete_foto_bitacora, name='delete_foto_bitacora'),

    # Endpoint para guardar las firmas (tanto de autor como de supervisor)  
    path('api/guardar_firmas/<int:id_proyecto>/', views.guardar_firmas_bitacora, name='guardar_firmas_bitacora'),
    
]