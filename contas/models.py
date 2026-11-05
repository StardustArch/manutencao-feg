from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    PAPEL_CHOICES = (
        ("utilizador", "Utilizador / Docente / Estudante"),
        ("tecnico", "Técnico de Manutenção"),
        ("admin", "Administrador"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil"
    )
    papel = models.CharField(
        max_length=20, choices=PAPEL_CHOICES, default="utilizador"
    )
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_papel_display()})"
