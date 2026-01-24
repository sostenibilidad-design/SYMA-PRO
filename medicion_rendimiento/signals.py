import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import MedicionCuadrilla

@receiver(post_delete, sender=MedicionCuadrilla)
def eliminar_foto_inicio(sender, instance, **kwargs):
    # Elimina la imagen física cuando se borra el registro
    if instance.foto_inicio:
        try:
            if os.path.isfile(instance.foto_inicio.path):
                os.remove(instance.foto_inicio.path)
        except Exception as e:
            print(f"⚠️ Error al borrar imagen: {e}")