from django import forms
from datetime import datetime
from .models import MedicionCuadrilla
from personal.models import Empleado
from .models import Cumplimiento,HistorialCambiosCuadrilla

class MedicionInicioForm(forms.ModelForm):
    class Meta:
        model = MedicionCuadrilla
        fields = [
            'cuadrilla',
            'empleados',
            'actividad',
            'ubicacion',
            'proyecto',
            'foto_inicio',
        ]
class MedicionFinForm(forms.ModelForm):
    class Meta:
        model = MedicionCuadrilla
        fields = [
            'hora_fin',
            'cantidad_producida',
        ]

class HistorialCambiosCuadrillaForm(forms.ModelForm):
    class Meta:
        model = HistorialCambiosCuadrilla
        fields = [
            'quien_salida',
            'quien_entro',
            'hora_salida',
            'hora_entrada'
        ]


class CumplimientoForm(forms.ModelForm):
    class Meta:
        model = Cumplimiento
        fields = [
            'cumplimiento_presupuestal', 
            'cumplimiento_programado',
            'actividad',
            'unidad_medida',
            ]