from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Perfil


@receiver(post_save, sender=User)
def criar_ou_atualizar_perfil_utilizador(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
    else:
        # Garante que se o perfil não existir por algum motivo antigo, ele é criado agora
        Perfil.objects.get_or_create(user=instance)
