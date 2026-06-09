from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Proyecto

@receiver(post_delete, sender=Proyecto)
def eliminar_imagen_portada(sender, instance, **kwargs):
    """
    Borra la imagen asociada físicamente (o en el bucket de DigitalOcean) 
    cuando se elimina el registro del proyecto en la base de datos.
    """
    if instance.imagen_portada:
        # El parámetro save=False es crucial, evita que Django intente 
        # actualizar la base de datos de un objeto que ya fue borrado.
        instance.imagen_portada.delete(save=False)