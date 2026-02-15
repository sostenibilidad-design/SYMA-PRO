import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import MedicionCuadrilla, ConfiguracionAlerta

@shared_task
def alerta_recordatorio_usuario():
    hoy = timezone.now().date()

    print(f"⏰ TAREA BEAT INICIADA (Recordatorio). Fecha: {hoy}")
    pendientes = MedicionCuadrilla.objects.filter(fecha=hoy, hora_fin__isnull=True)

    print(f"DEBUG: Ejecutando tarea 4:40 PM. Pendientes hoy: {pendientes.count()}")

    count = pendientes.count()
    print(f"📊 Pendientes encontrados: {count}")

    for m in pendientes:
        user_obj = m.usuario
        
        # Validamos que el usuario exista y tenga el campo 'correo'
        if user_obj and user_obj.correo:
            try:
                send_mail(
                    "SYMA - Recordatorio de Cierre de Actividad",
                    f"Hola {m.nombre_usuario},\n\nEste es un recordatorio del cierre de actividades del día de hoy para la actividad: {m.actividad} (Ubicación: {m.ubicacion}).\n\nPor favor, ingresa al sistema y registra el fin de la actividad.",
                    settings.DEFAULT_FROM_EMAIL,
                    [user_obj.correo], 
                    fail_silently=False
                )
                print(f"Enviado a: {user_obj.correo}")
            except Exception as e:
                print(f"Error enviando correo: {e}")
        else:
            print(f"ADVERTENCIA: El usuario {m.nombre_usuario} no tiene correo registrado.")

@shared_task
def alerta_incumplimiento_control():
    hoy = timezone.now().date()
    pendientes = MedicionCuadrilla.objects.filter(fecha=hoy, hora_fin__isnull=True)

    if pendientes.exists():
        print(f"DEBUG: Alerta Control - Encontradas {pendientes.count()} actividades sin cerrar.")

        config_alerta = ConfiguracionAlerta.objects.filter(tipo_alerta='Cierre diario').first()
        
        lista_correos = []

        if config_alerta:
            usuarios_asignados = config_alerta.destinatarios.all()
            
            for u in usuarios_asignados:
                if u.correo:
                    lista_correos.append(u.correo)
            
            print(f"DEBUG: Enviando reporte a {len(lista_correos)} destinatarios.")
        else:
            print("DEBUG: No existe configuración para 'Cierre diario'.")

        if lista_correos:
            items_resumen = []
            for m in pendientes:
                ubicacion = m.ubicacion if m.ubicacion else "Sin ubicación registrada"
                linea = f"- Actividad: {m.actividad} | Ubicación: {ubicacion} | A cargo: {m.nombre_usuario}"
                items_resumen.append(linea)
            
            resumen = "\n".join(items_resumen)

            try:
                send_mail(
                    "SYMA - Alerta: Actividades NO Finalizadas",
                    f"Atención,\n\nLas siguientes actividades del día de hoy NO han registrado su hora de fin:\n\n{resumen}\n\nPor favor verificar con los responsables.",
                    settings.DEFAULT_FROM_EMAIL,
                    lista_correos,
                    fail_silently=False
                )
                print("✅ Reporte enviado exitosamente.")
            except Exception as e:
                print(f"❌ Error enviando reporte: {e}")

