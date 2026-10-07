from django.contrib import admin
from .models import MedicionCuadrilla,HistorialCambiosCuadrilla,Cumplimiento,ConsumoAlimento

admin.site.register(MedicionCuadrilla)
admin.site.register(HistorialCambiosCuadrilla)
admin.site.register(Cumplimiento)
admin.site.register(ConsumoAlimento)
