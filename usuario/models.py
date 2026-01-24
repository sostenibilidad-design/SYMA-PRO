from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from personal.models import Empleado


class UsuarioManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError("El usuario debe tener un correo electrónico.")
        correo = self.normalize_email(correo)
        user = self.model(correo=correo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(correo, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    OPCIONES_REGISTRO = [
        ('manual', 'Registro manual'),
        ('seleccion', 'Registro por selección'),
    ]

    id = models.BigAutoField(primary_key=True)
    correo = models.EmailField(unique=True)
    tipo_registro = models.CharField(max_length=20, choices=OPCIONES_REGISTRO, default='manual')
    nombre_completo = models.CharField(max_length=150, null=True, blank=True)
    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    empleado = models.ForeignKey('personal.Empleado', on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')

    area_asignada = models.CharField(max_length=300, null=True, blank=True)
    permisos = models.JSONField(default=dict, blank=True)

    # flags
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    debe_cambiar_password = models.BooleanField(default=True)

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre_completo']
    objects = UsuarioManager()

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.nombre_visible or self.correo

    @property
    def nombre_visible(self):
        if self.tipo_registro == 'manual' and self.nombre_completo:
            return self.nombre_completo
        
        if self.tipo_registro == 'seleccion' and self.empleado:
            return self.empleado.nombre_completo
        
        return self.correo

    @property
    def primer_nombre(self):
        nombre = self.nombre_visible or ""
        return nombre.strip().split()[0]

    # === PERMISOS ============================================================
    def tiene_permiso(self, app, subarea=None, accion="ver"):
        if self.is_superuser:
            return True

        permisos = PermisoUsuario.objects.filter(
            usuario=self,
            funcionalidad__app=app
        )

        if subarea:
            permisos = permisos.filter(funcionalidad__submodulo=subarea)

        for p in permisos:
            if accion in p.acciones_permitidas:
                return True

        return False


class Funcionalidad(models.Model):
    app = models.CharField(max_length=100)
    submodulo = models.CharField(max_length=200)
    acciones = models.JSONField(default=list)

    class Meta:
        db_table = 'funcionalidades'
        unique_together = ('app', 'submodulo')

    def __str__(self):
        return f"{self.app} - {self.submodulo}"


class PermisoUsuario(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    funcionalidad = models.ForeignKey('Funcionalidad', on_delete=models.CASCADE)
    acciones_permitidas = models.JSONField(default=list)
    puede_asignar = models.BooleanField(default=False)

    class Meta:
        db_table = 'permisos_usuario'
        unique_together = ('usuario', 'funcionalidad')

    def __str__(self):
        return f"{self.usuario} → {self.funcionalidad.app}.{self.funcionalidad.submodulo}"
