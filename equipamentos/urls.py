from django.urls import path

from . import views

app_name = "equipamentos"

urlpatterns = [
    path("", views.equipamentos_lista, name="equipamentos_lista"),
    path("dashboard/", views.dashboard_metricas, name="dashboard"),
    path("relatorio/pdf/", views.relatorio_pdf, name="relatorio_pdf"),
    path("avarias/", views.avarias_lista, name="avarias_lista"),
    path("avarias/nova/", views.reportar_avaria, name="reportar_avaria"),
    path("avarias/minhas/", views.minhas_avarias, name="minhas_avarias"),
    path(
        "avarias/<int:pk>/",
        views.avaria_detalhe,
        name="avaria_detalhe",
    ),
    path(
        "avarias/<int:pk>/intervencao/",
        views.registar_intervencao,
        name="registar_intervencao",
    ),
    path(
        "avarias/<int:pk>/assumir/",
        views.assumir_avaria,
        name="avaria_assumir",
    ),
    path(
        "avarias/<int:pk>/estado/",
        views.alterar_estado_avaria,
        name="avaria_alterar_estado",
    ),
    path(
        "<int:pk>/reportar/",
        views.reportar_avaria_equipamento,
        name="reportar_avaria_equipamento",
    ),
    path(
        "<int:pk>/corrigir-estado/",
        views.corrigir_estado,
        name="corrigir_estado",
    ),
    path(
        "<int:pk>/qrcode.png",
        views.equipamento_qrcode,
        name="equipamento_qrcode",
    ),
    path(
        "<int:pk>/",
        views.equipamento_detalhe,
        name="equipamento_detalhe",
    ),
]
