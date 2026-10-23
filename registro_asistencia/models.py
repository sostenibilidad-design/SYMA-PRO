from django.db import models
from django.utils import timezone
from personal.models import Empleado
from proyectos.models import Proyecto
from usuario.models import Usuario


class MaestroAsistencia(models.Model):
    id = models.BigAutoField(primary_key=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='asistencias_diarias')
    fecha = models.DateField()
    estado = models.CharField(max_length=50, default='Borrador')
    creado_en = models.DateTimeField(default=timezone.now)

    usuario_creador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'asistencia_maestro'
        unique_together = ('proyecto', 'fecha')

    def __str__(self):
        return f"{self.proyecto.nombre} - {self.fecha}"

class RegistroEntradaSalida(models.Model):
    NOVEDADES = [
        ('Asistencia', 'Asistencia'),
        ('Ausentismo', 'Ausentismo'),
        ('Permiso no remunerado', 'Permiso no remunerado'),
        ('Sanción', 'Sanción'),
        ('Incapacidad general', 'Incapacidad general'),
        ('Incapacidad laboral', 'Incapacidad laboral'),
        ('Permiso remunerado', 'Permiso remunerado'),
        ('Vacaciones', 'Vacaciones'),
        ('Licencia', 'Licencia'),
        ('Retiro', 'Retiro'),
        ('Descanso', 'Descanso'),
    ]
    id_registro = models.BigAutoField(primary_key=True)
    maestro = models.ForeignKey(MaestroAsistencia, on_delete=models.CASCADE, related_name='registros_empleados')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='registros_asistencia')
    
    novedad = models.CharField(max_length=100, choices=NOVEDADES)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    horas_base = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    horas_comida = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    actividad = models.CharField(max_length=255, null=True, blank=True)
    
    comentario = models.TextField(null=True, blank=True)
    link_del_comentario = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'asistencia_registro_empleado'

    def __str__(self):
        return f"Registro {self.empleado.nombre_completo} - {self.novedad}"


class EntradaSalidaMultiple(models.Model):
    id_hora_multiple = models.BigAutoField(primary_key=True)
    registro = models.ForeignKey(RegistroEntradaSalida, on_delete=models.CASCADE, related_name='horas_multiples')
    
    hora_de_ingreso_multiple = models.TimeField()
    hora_de_salida_multiple = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'asistencia_horas_multiples'

class RegistroComida(models.Model):
    TIPOS_COMIDA = [
        ('Desayuno', 'Desayuno'),
        ('Almuerzo', 'Almuerzo'),
        ('Cena', 'Cena'),
    ]
    id_comida = models.BigAutoField(primary_key=True)
    registro = models.ForeignKey(RegistroEntradaSalida, on_delete=models.CASCADE, related_name='comidas')
    
    tipo_de_alimentacion = models.CharField(max_length=50, choices=TIPOS_COMIDA)
    hora_de_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'asistencia_comidas'

class HoraHistorica(models.Model):
    TIPO_HORAS = [
        ('Extras Diurnas', 'Extras Diurnas'),
        ('Extras Nocturnas', 'Extras Nocturnas'),
        ('Festivas Diurnas', 'Festivas Diurnas'),
        ('Festivas Nocturnas', 'Festivas Nocturnas'),
    ]

    id_hora_historica = models.BigAutoField(primary_key=True)
    registro = models.ForeignKey(RegistroEntradaSalida, on_delete=models.CASCADE, related_name='horas_historicas')
    
    tipo_de_horas = models.CharField(max_length=100, choices=TIPO_HORAS)
    # Pendiente = horas a favor del empleado; Deducir = saldo en contra
    accion = models.CharField(max_length=20, choices=[('Pendiente', 'Pendiente'), ('Deducir', 'Deducir')], default='Pendiente')
    cantidad_de_horas = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'asistencia_horas_historicas'

class Festivo(models.Model):
    """Festivo de Colombia descargado de la API (copia guardada para no consultarla en cada informe)."""
    fecha = models.DateField(unique=True)
    nombre = models.CharField(max_length=150, blank=True)

    class Meta:
        db_table = 'asistencia_festivo'
        ordering = ['fecha']

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y} {self.nombre}"


class AnioFestivos(models.Model):
    """Años cuyos festivos ya se descargaron, y cuándo fue la última vez."""
    anio = models.PositiveIntegerField(primary_key=True)
    actualizado_en = models.DateTimeField()

    class Meta:
        db_table = 'asistencia_anio_festivos'

    def __str__(self):
        return f"{self.anio} ({self.actualizado_en:%d/%m/%Y})"


class ParametroSistema(models.Model):
    horas_laborales_base = models.DecimalField(max_digits=4, decimal_places=2, default=8.40)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    
    modificado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'asistencia_parametro_sistema'
        verbose_name = 'Parámetro del Sistema'

    def save(self, *args, **kwargs):
        self.pk = 1 
        super(ParametroSistema, self).save(*args, **kwargs)

    def __str__(self):
        return f"Horas Base: {self.horas_laborales_base}"