from django.db import models
from personal.models import Empleado
from usuario.models import Usuario

# Modelo para la medición de rendimiento por cuadrilla

class MedicionCuadrilla(models.Model):
    OPCIONES_PROYECTO = [
        ('Ciudadela Andina', 'Ciudadela Andina'),
    ]

    id = models.BigAutoField(primary_key=True)

    proyecto = models.CharField(max_length=100, choices=OPCIONES_PROYECTO, default='Ciudadela Andina')
    fecha = models.DateField(auto_now_add=True)
    cuadrilla = models.CharField(max_length=100, verbose_name="Número de cuadrilla")
    numero_oficiales_ayudantes = models.CharField(max_length=100, blank=True, null=True)

    # Relaciones con Empleado y Usuario
    empleados = models.ManyToManyField(Empleado, blank=True, related_name='mediciones')
    empleado_cedula = models.CharField(max_length=500, null=True, blank=True, help_text="Cédulas de los empleados al momento del registro (para trazabilidad)")
    nombre_empleado = models.CharField(max_length=500, null=True, blank=True, help_text="Nombre del empleado al momento del registro (para trazabilidad)")

    usuario = models.ForeignKey( Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='mediciones_creadas')
    usuario_cedula = models.CharField(max_length=500, null=True, blank=True, help_text="Cédula del usuario que registró la medición")
    nombre_usuario = models.CharField( max_length=500, null=True,blank=True, help_text="Nombre del usuario que registró la medición")
    precio_hora_trabajadores = models.CharField(max_length=500, null=True, blank=True, help_text="Precio hora trabajadores al momento del registro (para trazabilidad)")

    actividad = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=100, null=True, blank=True)

    hora_inicio = models.TimeField(null=True, blank=True)
    hora_inicio_empleados = models.CharField(max_length=2000, null=True, blank=True, help_text="Horas de inicio granular por empleado ")
    hora_fin = models.TimeField(null=True, blank=True)
    hora_fin_empleados = models.CharField(max_length=2000, null=True, blank=True, help_text="Horas de fin granular por empleado ")

    horas_efectivas_trabajador = models.CharField(max_length=2000, null=True, blank=True, help_text="Horas efectivas por trabajador ")
    horas_trabajadas_totales = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    costo_total_oficiales = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    costo_total_ayudantes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_total_horas = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    cantidad_producida = models.FloatField (null=True, blank=True)
    rendimiento_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cumplimiento_presupuestal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cumplimiento_programado = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    comparacion_presupuestal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    comparacion_programado = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)   
    diferencia_presupuestal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    costo_por_unidad = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 

    foto_inicio = models.ImageField(upload_to='mediciones/inicio/', null=True, blank=True)
    foto_fin = models.ImageField(upload_to='mediciones/fin/', null=True, blank=True)

    class Meta:
        db_table = 'mediciones_cuadrilla'
        verbose_name = 'Medición de Cuadrilla'
        verbose_name_plural = 'Mediciones de Cuadrilla'
        ordering = ['-fecha', '-hora_inicio']

    def __str__(self):
        return f"Cuadrilla #{self.cuadrilla} - {self.actividad} ({self.fecha})"

class HistorialCambiosCuadrilla(models.Model):
    id = models.BigAutoField(primary_key=True)

    medicion = models.ForeignKey(MedicionCuadrilla,on_delete=models.CASCADE,related_name='historial_cambios')

    # Empleado que salió
    quien_salida = models.ForeignKey(Empleado,on_delete=models.SET_NULL,null=True,blank=True,related_name='salidas_historial')
    nombre_salida = models.CharField(max_length=500, null=True, blank=True)

    # Empleado que entró
    quien_entro = models.ForeignKey(Empleado,on_delete=models.SET_NULL,null=True,blank=True,related_name='entradas_historial')
    nombre_entrada = models.CharField(max_length=500, null=True, blank=True)

    fecha = models.DateField(auto_now_add=True)
    hora_salida = models.TimeField(null=True, blank=True)
    hora_entrada = models.TimeField(null=True, blank=True)

    # Quién registró el cambio
    usuario = models.ForeignKey(Usuario,on_delete=models.SET_NULL,null=True,blank=True)
    cedula_usuario = models.CharField(max_length=500, null=True, blank=True)
    nombre_usuario = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'historial_cambios_cuadrilla'
        ordering = ['-fecha','-id']

    def __str__(self):
        return f"Historial cambio — Medición {self.medicion.id}"


class Cumplimiento(models.Model):
    OPCIONES_UNIDAD = [
        ('u', 'u'),
        ('m³', 'm³'),
        ('m²', 'm²'),
        ('m', 'm'),
        ('kg', 'kg'),
    ]

    id = models.BigAutoField(primary_key=True)
    actividad = models.CharField(max_length=100)
    unidad_medida = models.CharField(max_length=100, choices=OPCIONES_UNIDAD, default='u')
    cumplimiento_presupuestal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cumplimiento_programado = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'cumplimientos'
        verbose_name = 'Cumplimiento'
        verbose_name_plural = 'Cumplimientos'

    def __str__(self):
        return f'Cumplimiento Presupuestal: {self.cumplimiento_presupuestal}%, Cumplimiento Programado: {self.cumplimiento_programado}%'

class ConsumoAlimento(models.Model):
    medicion = models.ForeignKey(MedicionCuadrilla, on_delete=models.CASCADE, related_name="consumos")
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="consumos_alimento")
    desayuno = models.BooleanField(default=False)
    almuerzo = models.BooleanField(default=False)

    class Meta:
        unique_together = ('medicion', 'empleado')

# Modelo para la medición de rendimiento individual

