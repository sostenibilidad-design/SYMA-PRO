import os

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import ejecutar_tareas_cron, login_admin_limitado

# La ruta del panel de administración se puede cambiar con la variable ADMIN_URL (ej.: «panel-syma-x7k2/») para que no sea /admin/
RUTA_ADMIN = os.environ.get('ADMIN_URL', 'admin/').strip('/') + '/'

urlpatterns = [
    path(RUTA_ADMIN + 'login/', login_admin_limitado, name='admin_login_limitado'),   # antes que el resto del panel
    path(RUTA_ADMIN, admin.site.urls),
    path('', include('core.urls')),
    path('personal/', include('personal.urls')),
    path('usuario/', include('usuario.urls')),
    path('medicion_rendimiento/', include('medicion_rendimiento.urls')),
    path('proyectos/', include('proyectos.urls')),
    path('bitacora/', include('bitacora.urls')),
    path('cron/<str:nombre_tarea>/', ejecutar_tareas_cron, name='cron_tasks'),
    path('registro-asistencia/', include('registro_asistencia.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

