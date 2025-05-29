# user/urls.py (actualizado con las nuevas rutas)

from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
from .views import ContraseñaConf
from .email_utils import enviar_correo_reset_async


# Clase personalizada para el reset de contraseña
class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'user/password_reset/password_reset.html'
    success_url = reverse_lazy('user:password_reset_done')
    email_template_name = 'user/password_reset/password_reset_email.html'
    subject_template_name = 'user/password_reset/password_reset_subject.txt'

    def form_valid(self, form):
        """Override para usar nuestra función personalizada de email"""
        # Obtener el usuario
        email = form.cleaned_data['email']
        from django.contrib.auth.models import User

        try:
            user = User.objects.get(email=email)

            # Generar token y uid
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.encoding import force_bytes
            from django.utils.http import urlsafe_base64_encode

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            domain = self.request.get_host()
            protocol = 'https' if self.request.is_secure() else 'http'

            # Enviar correo personalizado
            enviar_correo_reset_async(user, uid, token, domain, protocol)

        except User.DoesNotExist:
            pass  # No revelar si el email existe o no

        # Redirigir a la página de confirmación
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.get_success_url())


app_name = 'user'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('perfiles/crear/', views.create_perfil, name='create_perfil'),
    path('perfiles/<int:pk>/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfiles/<int:pk>/eliminar/', views.eliminar_perfil, name='eliminar_perfil'),
    path('perfiles/<int:pk>/eliminar-ajax/', views.eliminar_perfil_ajax, name='eliminar_perfil_ajax'),
    path('perfil-list/', views.perfil_list, name='perfil_list'),
    path('perfiles/', views.perfil_list, name='perfil_list'),
    path('loading/', views.loading_view, name='loading'),
    path('dashboard-data/', views.dashboard_data_view, name='dashboard_data'),

    # Recuperación de contraseña - USANDO NUESTRA CLASE PERSONALIZADA
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user/password_reset/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', ContraseñaConf.as_view(
        template_name='user/password_reset/password_reset_confirm.html',
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user/password_reset/password_reset_complete.html'
    ), name='password_reset_complete'),
]