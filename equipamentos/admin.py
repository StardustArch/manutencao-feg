from django.contrib import admin
from .models import Equipamento, Avaria, Intervencao

admin.site.register(Equipamento)
admin.site.register(Avaria)
admin.site.register(Intervencao)
