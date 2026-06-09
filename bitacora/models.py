from django.db import models
from proyectos.models import Proyecto
from usuario.models import Usuario

class Bitacora(models.Model):
    id_bitacora = models.BigAutoField(primary_key=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='bitacoras')
    fecha = models.DateField(null=True, blank=True)
    
    # Clima
    clima_manana = models.CharField(max_length=20, null=True, blank=True)
    clima_tarde = models.CharField(max_length=20, null=True, blank=True)
    
    # Textos
    equipo_obra = models.TextField(null=True, blank=True)
    actividades = models.TextField(null=True, blank=True)
    
    # Contadores de personal
    cant_maestros = models.IntegerField(default=0)
    cant_oficiales = models.IntegerField(default=0)
    cant_ayudantes = models.IntegerField(default=0)
    cant_contratistas = models.IntegerField(default=0)
    
    # Firmas (Se llenarán al final con la modal)
    autor = models.ForeignKey(Usuario, related_name='bitacoras_autor', on_delete=models.SET_NULL, null=True, blank=True)
    firma_autor_url = models.ImageField(upload_to='bitacoras/firmas/', null=True, blank=True)
    supervisor = models.ForeignKey(Usuario, related_name='bitacoras_supervisor', on_delete=models.SET_NULL, null=True, blank=True)
    firma_supervisor_url = models.ImageField(upload_to='bitacoras/firmas/', null=True, blank=True)

    # Campos de control interno
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bitacora'
        ordering = ['creado_en'] # Orden cronológico para las páginas

class BitacoraFoto(models.Model):
    id_bitacora_fotos = models.BigAutoField(primary_key=True)
    bitacora = models.ForeignKey(Bitacora, related_name='fotos', on_delete=models.CASCADE)
    url_imagen = models.ImageField(upload_to='bitacoras/fotos/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bitacora_fotos'
