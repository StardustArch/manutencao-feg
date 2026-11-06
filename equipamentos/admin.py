from django.contrib import admin

from .models import Avaria, Equipamento, HistoricoEstadoEquipamento, Intervencao


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    readonly_fields = ("estado",)


@admin.register(Avaria)
class AvariaAdmin(admin.ModelAdmin):
    list_display = ("equipamento", "estado", "prioridade", "reportado_por")


@admin.register(HistoricoEstadoEquipamento)
class HistoricoEstadoEquipamentoAdmin(admin.ModelAdmin):
    list_display = (
        "equipamento",
        "estado_anterior",
        "estado_novo",
        "alterado_por",
        "data_hora",
    )
    readonly_fields = (
        "equipamento",
        "estado_anterior",
        "estado_novo",
        "alterado_por",
        "origem",
        "motivo",
        "data_hora",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Intervencao)
