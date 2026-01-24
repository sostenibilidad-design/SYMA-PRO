from django import forms
from .models import Usuario
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        exclude = [
            'password', 'last_login', 'groups', 'user_permissions',
            'fecha_creacion', 'ultima_modificacion', 'rol'
        ]

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Correo", max_length=254)

    def get_users(self, email):
        """
        Retorna los usuarios activos cuyo campo 'correo' coincide con el ingresado.
        """
        active_users = User._default_manager.filter(correo__iexact=email, is_active=True)
        return (u for u in active_users if u.has_usable_password())

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        if not User.objects.filter(correo__iexact=email, is_active=True).exists():
            raise forms.ValidationError("No existe ningún usuario con este correo.")
        return cleaned_data