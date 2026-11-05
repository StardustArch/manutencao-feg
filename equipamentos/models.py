from django.contrib.auth.models import User
from django.db import models


class Equipamento(models.Model):
    TIPO_CHOICES = (
        ("computador", "Computador / Desktop"),
        ("laptop", "Portátil"),
        ("projetor", "Projetor"),
        ("impressora", "Impressora"),
        ("outro", "Outro Periférico"),
    )

    ESTADO_EQUIPAMENTO_CHOICES = (
        ("operacional", "Operacional"),
        ("avariado", "Avariado"),
        ("manutencao", "Em Manutenção"),
        ("abatido", "Abatido"),
    )

    codigo = models.CharField(
        max_length=50,
        unique=True,
        help_text="Código de património ou etiqueta (ex: UCM-FEG-PC-01)",
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    marca_modelo = models.CharField(max_length=100)
    localizacao = models.CharField(
        max_length=100, default="Laboratório de Informática UCM-FEG"
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_EQUIPAMENTO_CHOICES, default="operacional"
    )
    data_aquisicao = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.marca_modelo}"


class Avaria(models.Model):
    PRIORIDADE_CHOICES = (
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("urgente", "Urgente"),
    )

    ESTADO_AVARIA_CHOICES = (
        ("pendente", "Pendente"),
        ("em_reparacao", "Em Reparação"),
        ("resolvido", "Resolvido"),
        ("cancelado", "Cancelado"),
    )

    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.CASCADE, related_name="avarias"
    )
    reportado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="avarias_reportadas"
    )
    tecnico_atribuido = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avarias_atribuidas",
    )

    descricao = models.TextField(help_text="Descreva o problema detalhadamente")
    prioridade = models.CharField(
        max_length=20, choices=PRIORIDADE_CHOICES, default="media"
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_AVARIA_CHOICES, default="pendente"
    )

    data_registo = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Avaria #{self.id} - {self.equipamento.codigo} ({self.get_estado_display()})"


class Intervencao(models.Model):
    avaria = models.ForeignKey(
        Avaria, on_delete=models.CASCADE, related_name="intervencoes"
    )
    tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    detalhes_reparacao = models.TextField(
        help_text="O que foi feito para resolver o problema"
    )
    pecas_substituidas = models.TextField(
        blank=True, null=True, help_text="Peças usadas, se aplicável"
    )
    data_intervencao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Intervenção em {self.avaria.equipamento.codigo} por"
            f" {self.tecnico.username if self.tecnico else 'N/D'}"
        )
