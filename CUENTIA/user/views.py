# user/views.py (versión actualizada con editar y eliminar)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import PerfilForm, RegistroForm, LoginForm
from .models import Perfil
from .email_utils import enviar_correo_bienvenida_async
import logging

logger = logging.getLogger(__name__)


@login_required
def create_perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST)
        if form.is_valid():
            perfil = form.save(commit=False)
            perfil.usuario = request.user
            perfil.save()
            messages.success(request, f'¡Perfil de {perfil.nombre} creado exitosamente!')
            # Redirigir a la lista de perfiles después de crear
            return redirect('user:perfil_list')
    else:
        # Limpiar mensajes existentes cuando se accede al formulario
        storage = messages.get_messages(request)
        storage.used = True  # Marca todos los mensajes como usados para limpiarlos
        form = PerfilForm()

    return render(request, 'user/create_perfil.html', {'form': form})


@login_required
def editar_perfil(request, pk):
    """Vista para editar un perfil existente"""
    perfil = get_object_or_404(Perfil, pk=pk, usuario=request.user)

    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡Perfil de {perfil.nombre} actualizado exitosamente!')
            return redirect('user:perfil_list')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Limpiar mensajes existentes cuando se accede al formulario de edición
        storage = messages.get_messages(request)
        storage.used = True
        form = PerfilForm(instance=perfil)

    return render(request, 'user/editar_perfil.html', {
        'form': form,
        'perfil': perfil,
        'is_editing': True
    })


@login_required
def eliminar_perfil(request, pk):
    """Vista para eliminar un perfil"""
    perfil = get_object_or_404(Perfil, pk=pk, usuario=request.user)

    if request.method == 'POST':
        nombre_perfil = perfil.nombre
        perfil.delete()
        messages.success(request, f'Perfil de {nombre_perfil} eliminado exitosamente.')
        return redirect('user:perfil_list')

    return render(request, 'user/eliminar_perfil.html', {'perfil': perfil})


@login_required
@require_POST
def eliminar_perfil_ajax(request, pk):
    """Vista AJAX para eliminar perfil con confirmación"""
    try:
        perfil = get_object_or_404(Perfil, pk=pk, usuario=request.user)
        nombre_perfil = perfil.nombre
        perfil.delete()

        return JsonResponse({
            'success': True,
            'message': f'Perfil de {nombre_perfil} eliminado exitosamente.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error al eliminar el perfil. Inténtalo de nuevo.'
        })


@login_required
def perfil_list(request):
    """Vista para listar perfiles infantiles"""
    perfiles = Perfil.objects.filter(usuario=request.user)
    return render(request, 'user/perfil_list.html', {'perfiles': perfiles})


class ContraseñaConf(PasswordResetConfirmView):
    template_name = 'user/password_reset/password_reset_confirm.html'
    success_url = reverse_lazy('user:login')

    def form_valid(self, form):
        messages.success(self.request, "¡Contraseña cambiada exitosamente! Ahora podés iniciar sesión.")
        return super().form_valid(form)


def logout_view(request):
    logout(request)
    return redirect('landing')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, f'Bienvenido, {form.get_user().username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = LoginForm()

    return render(request, 'user/login.html', {'form': form})


def registro_view(request):
    """Vista para la página de registro con envío automático de correo de bienvenida"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            # Guardar el usuario
            user = form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            print(f"🔄 Usuario creado: {username} - Email: {email}")

            # ===== ENVIAR CORREO DE BIENVENIDA =====
            try:
                from .email_utils import enviar_correo_bienvenida_async
                # Enviar correo de bienvenida de forma asíncrona
                enviar_correo_bienvenida_async(user)
                print(f"📧 Proceso de envío de correo iniciado para {email}")
                logger.info(f"Proceso de envío de correo iniciado para {email}")
            except Exception as e:
                print(f"❌ Error al iniciar envío de correo para {email}: {str(e)}")
                logger.error(f"Error al iniciar envío de correo para {email}: {str(e)}")
                # No mostramos el error al usuario para no afectar la experiencia

            # Mensaje de éxito
            messages.success(
                request,
                f'¡Cuenta creada para {username}! Te hemos enviado un correo de bienvenida a {email}.'
            )
            return redirect('user:login')
        else:
            # Mostrar errores específicos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = RegistroForm()

    return render(request, 'user/register.html', {'form': form})


# loading (cargando antes de entra a la oagina principal)

@login_required
def loading_view(request):
    """Vista para la pantalla de carga después del login"""
    return render(request, 'user/loading.html')


@login_required
def dashboard_data_view(request):
    """Vista que simula la carga de datos del dashboard"""
    import time
    import json
    from django.http import JsonResponse

    # Simular tiempo de carga (puedes ajustar o quitar esto)
    time.sleep(2)

    # Aquí puedes cargar datos reales del dashboard
    # Por ejemplo: perfiles, cuentos recientes, estadísticas, etc.

    data = {
        'success': True,
        'message': 'Datos cargados exitosamente',
        'redirect_url': '/dashboard/'  # URL del dashboard
    }

    return JsonResponse(data)


# Modificar la vista login_view existente
def login_view(request):
    if request.user.is_authenticated:
        return redirect('user:loading')  # Cambiar aquí

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, f'Bienvenido, {form.get_user().username}!')
            return redirect('user:loading')  # Cambiar aquí también
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = LoginForm()

    return render(request, 'user/login.html', {'form': form})