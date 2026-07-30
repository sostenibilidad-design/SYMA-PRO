from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import ejecutar_tareas_cron

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('personal/', include('personal.urls')),
    path('usuario/', include('usuario.urls')),
    path('medicion_rendimiento/', include('medicion_rendimiento.urls')),
    path('proyectos/', include('proyectos.urls')),
    path('bitacora/', include('bitacora.urls')),
    path('cron/<str:nombre_tarea>/', ejecutar_tareas_cron, name='cron_tasks'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

