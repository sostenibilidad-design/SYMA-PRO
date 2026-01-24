from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CorreoBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        print("🚨 authenticate() ejecutado")
        print("username:", username)
        print("password:", password)

        if username is None or password is None:
            return None

        try:
            user = User.objects.get(correo=username)
            print("✅ Usuario encontrado:", user)
        except User.DoesNotExist:
            print("❌ Usuario NO existe")
            return None

        if not user.check_password(password):
            print("🔓 Password incorrecta")
            return None

        if not self.user_can_authenticate(user):
            print("🔴 Usuario inactivo")
            return None

        print("🟢 Autenticación exitosa")
        return user
