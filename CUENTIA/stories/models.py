#stories/models.py
from django.db import models
from django.contrib.auth.models import User
from user.models import Perfil


class Cuento(models.Model):
    ESTADO_CHOICES = [
        ('generando', 'Generando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]

    LONGITUD_CHOICES = [
        ('corto', 'Corto (2-3 minutos)'),
        ('medio', 'Medio (5-7 minutos)'),
        ('largo', 'Largo (10-15 minutos)'),
    ]

    TEMA_CHOICES = [
        ('aventura', 'Aventura'),
        ('fantasia', 'Fantasía'),
        ('amistad', 'Amistad'),
        ('familia', 'Familia'),
        ('naturaleza', 'Naturaleza'),
        ('ciencia', 'Ciencia Ficción'),
        ('animales', 'Animales'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cuentos')
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='cuentos', null=True, blank=True)

    # Datos del formulario
    titulo = models.CharField(max_length=200)
    personaje_principal = models.CharField(max_length=100)
    tema = models.CharField(max_length=50, choices=TEMA_CHOICES)
    edad = models.CharField(max_length=20)
    longitud = models.CharField(max_length=20, choices=LONGITUD_CHOICES)

    # Contenido generado
    contenido = models.TextField(blank=True)
    moraleja = models.TextField(blank=True)
    imagen_url = models.URLField(blank=True)
    imagen_prompt = models.TextField(blank=True)

    # Audio
    audio_url = models.URLField(blank=True)

    # Metadatos
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='generando')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    es_favorito = models.BooleanField(default=False)

    # Estadísticas
    veces_leido = models.IntegerField(default=0)
    tiempo_lectura_estimado = models.IntegerField(default=0)  # en segundos

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"

    def marcar_como_leido(self):
        """Incrementa el contador de lecturas"""
        self.veces_leido += 1
        self.save()

    def toggle_favorito(self):
        """Alterna el estado de favorito"""
        self.es_favorito = not self.es_favorito
        self.save()
        return self.es_favorito


class EstadisticaLectura(models.Model):
    """Modelo para trackear estadísticas de lectura por usuario"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cuento = models.ForeignKey(Cuento, on_delete=models.CASCADE)
    fecha_lectura = models.DateTimeField(auto_now_add=True)
    tiempo_lectura = models.IntegerField(default=0)  # en segundos
    tipo_lectura = models.CharField(max_length=20, choices=[
        ('texto', 'Lectura de Texto'),
        ('audio', 'Escucha de Audio'),
    ], default='texto')

    class Meta:
        ordering = ['-fecha_lectura']
