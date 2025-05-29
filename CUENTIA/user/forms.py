from django import forms
# user/forms.py - Versión actualizada

from .models import Perfil
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class LoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _(
            "Usuario o contraseña incorrectos. Por favor, intenta de nuevo."
        ),
        'inactive': _("Esta cuenta está desactivada."),
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise forms.ValidationError(
                    _("El usuario no está registrado."),
                    code='invalid_username',
                )
            else:
                user = authenticate(username=username, password=password)
                if user is None:
                    raise forms.ValidationError(
                        _("La contraseña es incorrecta."),
                        code='invalid_password',
                    )

        return super().clean()


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre', 'edad', 'genero', 'temas_preferidos', 'personajes_favoritos']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el nombre del niño/a'
            }),
            'edad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 18,
                'placeholder': 'Edad en años'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-control'
            }),
            'temas_preferidos': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ejemplo: amistad, aventura, misterio, fantasía, ciencia ficción'
            }),
            'personajes_favoritos': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ejemplo: robots, héroes, dragones, princesas, animales'
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'edad': 'Edad',
            'genero': 'Género',
            'temas_preferidos': 'Temas de cuentos preferidos',
            'personajes_favoritos': 'Personajes que te gusten',
        }


class RegistroForm(UserCreationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        help_text="Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ingresa tu nombre de usuario'}),
        error_messages={
            'required': 'El nombre de usuario es obligatorio.',
            'max_length': 'El nombre de usuario no puede tener más de 150 caracteres.'
        }
    )
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        required=True,  # Aseguramos que sea obligatorio
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Ingresa tu correo electrónico'}),
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Por favor ingresa un correo electrónico válido.'
        }
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Ingresa tu contraseña'}),
        error_messages={
            'required': 'La contraseña es obligatoria.',
            'min_length': 'La contraseña debe tener al menos 8 caracteres.'
        }
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirma tu contraseña'}),
        error_messages={
            'required': 'Es obligatorio confirmar la contraseña.',
            'password_mismatch': 'Las contraseñas no coinciden.',
            'password_too_similar': 'La contraseña no puede ser demasiado similar al nombre de usuario.'
        }
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')

        # Validar que no contenga números
        if any(char.isdigit() for char in username):
            raise ValidationError("El nombre de usuario no debe contener números.")

        # Verificar si ya existe un usuario con ese nombre
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso.")

        return username

    def clean_email(self):
        """Validar que el email no esté ya registrado"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    def save(self, commit=True):
        """Guardar el usuario con el email"""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")