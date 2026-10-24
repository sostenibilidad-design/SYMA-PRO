from django.contrib import admin
from .models import RegistroEntradaSalida, MaestroAsistencia, Festivo, AnioFestivos

admin.site.register(MaestroAsistencia)
admin.site.register(RegistroEntradaSalida)
admin.site.register(Festivo)
admin.site.register(AnioFestivos)
