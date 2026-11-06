from django.contrib import admin
from .models import Avaria, Equipamento, HistoricoEstadoEquipamento, Intervencao

admin.site.register(Equipamento)
admin.site.register(Avaria)
admin.site.register(Intervencao)
admin.site.register(HistoricoEstadoEquipamento)
