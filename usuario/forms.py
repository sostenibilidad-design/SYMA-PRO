from django import forms
from .models import Usuario
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        # Lista blanca: is_superuser, is_staff, is_active, permisos y debe_cambiar_password los decide el servidor,
        # nunca el formulario (si no, quien envíe el POST puede hacerse administrador).
        fields = ['tipo_registro', 'nombre_completo', 'cedula', 'cargo', 'empleado', 'correo', 'area_asignada']

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Correo", max_length=254)

    def get_users(self, email):
        """
        Retorna los usuarios activos cuyo campo 'correo' coincide con el ingresado.
        """
        active_users = User._default_manager.filter(correo__iexact=email, is_active=True)
        return (u for u in active_users if u.has_usable_password())
    # Sin clean() que avise si el correo existe: la respuesta es la misma exista o no la cuenta (evita enumerar correos).