from django import forms
from .models import Empleado

class Personalform(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = '__all__'