from django import forms
from datetime import datetime
from .models import MedicionCuadrilla
from personal.models import Empleado
from .models import Cumplimiento,HistorialCambiosCuadrilla, ConfiguracionAlerta

class MedicionInicioForm(forms.ModelForm):
    class Meta:
        model = MedicionCuadrilla
        fields = [
            'empleados',
            'actividad',
            'foto_inicio',
            'hora_inicio',
        ]
class MedicionFinForm(forms.ModelForm):
    class Meta:
        model = MedicionCuadrilla
        fields = [
            'hora_fin',
            'cantidad_producida',
            'ubicacion',
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

class ConfiguracionAlertaForm(forms.ModelForm):

    class Meta:
        model = ConfiguracionAlerta
        fields = [
            'tipo_alerta', 
            'destinatarios',
            'nombre_usuario',
            'correo',
            ]