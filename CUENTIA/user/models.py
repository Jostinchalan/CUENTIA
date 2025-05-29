from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Perfil(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='perfiles_infantiles')
    nombre = models.CharField(max_length=30)
    edad = models.PositiveSmallIntegerField()
    GENEROS = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('N', 'No especificado'),
    ]
    genero = models.CharField(max_length=1, choices=GENEROS, default='N')

    # Nuevos campos reemplazando 'intereses'
    temas_preferidos = models.TextField(
        blank=True,
        verbose_name="Temas de cuentos preferidos",
        help_text="Ejemplo: amistad, aventura, misterio"
    )
    personajes_favoritos = models.TextField(
        blank=True,
        verbose_name="Personajes preferidos",
        help_text="Ejemplo: robots, héroes, dragones"
    )

    def temas_lista(self):
        """Devuelve la lista de temas preferidos ya limpios."""
        return [tema.strip() for tema in self.temas_preferidos.split(',') if tema.strip()]

    def personajes_lista(self):
        """Devuelve la lista de personajes favoritos ya limpios."""
        return [personaje.strip() for personaje in self.personajes_favoritos.split(',') if personaje.strip()]

    def __str__(self):
        return f"{self.nombre} ({self.get_genero_display()})"