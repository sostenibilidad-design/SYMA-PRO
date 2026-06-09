from django import forms
from .models import Proyecto

class ProyectoForm(forms.ModelForm):

    class Meta:
        model = Proyecto
        fields = [
            'nombre',
            'ubicacion',
            'imagen_portada',
            'estado',
            'cant_viviendas',
            'm2_zona_verde',
            'm2_urbanismo',
            'numero_pisos',
            'numero_bloques',
            'sistema_constructivo',
            'link_planos',
            'cant_empleados',
        ]