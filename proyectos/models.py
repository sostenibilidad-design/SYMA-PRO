from django.db import models

class Proyecto(models.Model):
    # Opciones predefinidas para el semáforo de colores
    ESTADOS_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('PAUSADO', 'Pausado'),
        ('TERMINADO', 'Terminado'),
        ('ESCRITURACION', 'Escrituracion'),
    ]

    id_proyectos = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    ubicacion = models.CharField(max_length=100)
    
    imagen_portada = models.ImageField(upload_to='proyectos/portadas/', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='ACTIVO')
    
    cant_viviendas = models.IntegerField(default=0)
    m2_zona_verde = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    m2_urbanismo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    numero_pisos = models.IntegerField(default=0)
    numero_bloques = models.IntegerField(default=0)
    sistema_constructivo = models.CharField(max_length=100)
    link_planos = models.URLField(max_length=500)
    cant_empleados = models.IntegerField(default=0) # Por ahora en 0, luego se puede calcular

    class Meta:
        db_table = 'proyectos'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def __str__(self):
        return self.nombre