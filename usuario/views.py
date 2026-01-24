import random
import string
import json
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash


from .forms import UsuarioForm
from .models import Usuario, Funcionalidad
from personal.models import Empleado
from usuario.utils import sincronizar_permisos_usuario, eliminar_permisos_usuario

def generar_contraseña(longitud=6):
    """Genera una contraseña aleatoria segura."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choices(caracteres, k=longitud))

@login_required
def usuario(request):
    user = request.user  # Usuario actual logueado

    usuarios = Usuario.objects.all()

    if request.method == "POST":
        seleccion = request.POST.get("elemento")
        accion = request.POST.get("accion")
        ids = [int(x) for x in seleccion.split(",") if x.strip().isdigit()] if seleccion else []

        if accion == "actualizar" and ids:
            pk = ids[0]
            return redirect("actualizar", pk=pk)

        elif accion == "borrar" and ids:
                for user_id in ids:
                    usuario_eliminar = Usuario.objects.filter(pk=user_id).first()
                    if usuario_eliminar:
                        usuario_eliminar.delete()
                messages.success(request, "Usuario(s) eliminado(s) correctamente.")

    cantidad_filas_vacias = max (0, 20 - usuarios.count())

    funcionalidades = Funcionalidad.objects.all().order_by('app', 'submodulo')
    tree = {}
    for f in funcionalidades:
        tree.setdefault(f.app, {})
        tree[f.app][f.submodulo] = f.acciones or []


    context = {
        "usuarios": usuarios,
        "filas_vacias": range(cantidad_filas_vacias),
        "tree": tree,
    }

    return render(request, 'usuario/usuario.html',context)

def registrar_usuario (request):

    empleados = Empleado.objects.all()
    funcionalidades = Funcionalidad.objects.all().order_by('app', 'submodulo')
    tree = {}

    for f in funcionalidades:
        tree.setdefault(f.app, {})
        tree[f.app][f.submodulo] = f.acciones or []

    if request.method == "POST":
        form = UsuarioForm(request.POST)
        
        if form.is_valid():

            usuario = form.save(commit=False)

            if usuario.tipo_registro == 'seleccion' and usuario.empleado:                
                usuario.nombre_completo = usuario.empleado.nombre_completo
                usuario.cedula = usuario.empleado.cedula
                usuario.cargo = usuario.empleado.cargo

            # Validar correo
            correo = usuario.correo.strip() if usuario.correo else ''
            if not correo:
                messages.error(request, "El campo correo es obligatorio.")
                return redirect('registrar_usuario')

            if Usuario.objects.filter(correo=correo).exists():
                messages.error(request, "Ya existe un usuario con ese correo.")
                return redirect('registrar_usuario')

            # --- Generar contraseña temporal ---
            contraseña_temporal = generar_contraseña()
            usuario.set_password(contraseña_temporal)  # se guarda cifrada

            usuario.is_active = True                  
            usuario.debe_cambiar_password = True 

            # Armar estructura de permisos
            permisos = {}
            for area, subareas in tree.items():
                for sub, acciones in subareas.items():
                    key = f"perm__{area}__{sub}"
                    seleccionadas = request.POST.getlist(key)
                    
                    if seleccionadas:
                        if 'ver' not in seleccionadas:
                            seleccionadas.append('ver')
                        permisos.setdefault(area, {})
                        permisos[area][sub] = seleccionadas

            usuario.permisos = permisos
            usuario.save()
            sincronizar_permisos_usuario(usuario)

            # --- Enviar correo con la contraseña ---
            contexto = {
                'nombre': usuario.nombre_completo or 'Usuario',
                'correo': usuario.correo,
                'contraseña': contraseña_temporal,
            }

            html_content = render_to_string('usuario/correo_bienvenida.html', contexto)
            asunto = "Bienvenido al sistema de SYMA"
            remitente = "sostenibilidad@syma.com.co"
            destinatarios = [usuario.correo]

            email = EmailMultiAlternatives(asunto, '', remitente, destinatarios)
            email.attach_alternative(html_content, "text/html")
            email.send()

            messages.success(request, "Usuario registrado con permisos asignados correctamente.")
            return redirect('usuario')
    else:
        form = UsuarioForm()

    context = {
        "form": form,
        "empleados": empleados,
        "tree": tree,
    }
    return render(request, "usuario/registrar_usuario.html", context)


def actualizar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    # Obtener todas las funcionalidades para construir el árbol
    funcionalidades = Funcionalidad.objects.all().order_by('app', 'submodulo')
    tree = {}
    for f in funcionalidades:
        tree.setdefault(f.app, {})
        tree[f.app][f.submodulo] = f.acciones or []

    # Convertir área asignada en lista para la plantilla
    usuario_areas = [a.strip() for a in usuario.area_asignada.split(',')] if usuario.area_asignada else []

    # Preparar permisos para el template de forma que no use .get() en el HTML
    usuario_permisos = {
        area: {
            sub: usuario.permisos.get(area, {}).get(sub, [])
            for sub in subareas.keys()
        } for area, subareas in tree.items()
    }
    if request.method == "POST":
        # --- Guardar áreas asignadas ---
        areas_seleccionadas = request.POST.getlist("area_asignada")

        if areas_seleccionadas:
            usuario.area_asignada = ", ".join(areas_seleccionadas)
        
        # --- Reconstruir estructura de permisos ---
        permisos = {}
        for area, subareas in tree.items():
            for sub, acciones in subareas.items():
                key = f"perm__{area}__{sub}"
                seleccionadas = request.POST.getlist(key)
                
                if seleccionadas:
                    if 'ver' not in seleccionadas:
                        seleccionadas.append('ver')
                    permisos.setdefault(area, {})
                    permisos[area][sub] = seleccionadas
        
        usuario.permisos = permisos
        usuario.save()
        sincronizar_permisos_usuario(usuario)
        messages.success(request, "Usuario actualizado correctamente.")

        # Si usas modal con AJAX, podemos devolver JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"status": "ok"})
        
        return redirect("usuario")

    context = {
        "usuario": usuario,
        "tree": tree,
        "usuario_areas": usuario_areas,
        "usuario_permisos": usuario_permisos, 
    }

    return render(request, "usuario/actualizar_usuario.html", context)

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('home')

        user = request.user
        user.set_password(password1)
        user.debe_cambiar_password = False
        user.save()

        update_session_auth_hash(request, user)
        
        messages.success(request, 'Contraseña actualizada correctamente. Debes iniciar sesión nuevamente.')
        return redirect('home')

    return redirect('home')
