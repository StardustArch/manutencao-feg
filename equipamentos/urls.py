from django.urls import path

from . import views

app_name = "equipamentos"

urlpatterns = [
    path("", views.equipamentos_lista, name="equipamentos_lista"),
    path("dashboard/", views.dashboard_metricas, name="dashboard"),
    path("relatorio/pdf/", views.relatorio_pdf, name="relatorio_pdf"),
    path("avarias/", views.avarias_lista, name="avarias_lista"),
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
