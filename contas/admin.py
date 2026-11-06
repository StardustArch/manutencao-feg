from django.contrib import admin

from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "papel", "telefone")
    list_display_links = ("user",)
    list_editable = ["papel"]
