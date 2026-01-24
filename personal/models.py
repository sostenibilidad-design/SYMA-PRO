from django.db import models

class Empleado(models.Model):
    cedula = models.CharField(max_length=20, primary_key=True, unique=True)
    nombre_completo = models.CharField(max_length=150, null=True, blank=True)
    cargo = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'empleados'  # Nombre explícito de la tabla en la BD
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return f"{self.nombre_completo} - {self.cargo}"

class ValorHora(models.Model):
    ayudante_raso = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ayudante_entendido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    oficial_junior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    oficial_senior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'valores_hora'
        verbose_name = 'Valor Hora'
        verbose_name_plural = 'Valores Hora'