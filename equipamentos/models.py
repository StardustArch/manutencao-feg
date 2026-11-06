from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


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

    def get_absolute_url(self):
        """Página pública (para utilizadores autenticados) deste equipamento.

        É este URL que fica gravado no QR code. Usamos o `reverse` do Django
        para que o endereço acompanhe automaticamente alterações nas rotas.
        """
        return reverse(
            "equipamentos:equipamento_detalhe",
            kwargs={"pk": self.pk},
        )


def recalcular_estado_equipamento(equipamento, actor=None, origem="fluxo", motivo=""):
    """Sincroniza o estado do equipamento com as avarias ainda abertas.

    O estado alvo é sempre derivado do trabalho pendente:
      * existe alguma avaria em reparação -> "manutencao";
      * caso contrário, existe alguma avaria pendente -> "avariado";
      * caso contrário -> "operacional".

    REGRA DE OURO: um equipamento abatido só pode sair desse estado através de
    uma correção manual (``origem="manual"``). O fluxo automático nunca o
    reativa. Quando o estado não muda, nada é gravado.
    """
    if equipamento.estado == "abatido" and origem != "manual":
        return equipamento.estado

    if equipamento.avarias.filter(estado="em_reparacao").exists():
        novo_estado = "manutencao"
    elif equipamento.avarias.filter(estado="pendente").exists():
        novo_estado = "avariado"
    else:
        novo_estado = "operacional"

    if novo_estado == equipamento.estado:
        return equipamento.estado

    estado_anterior = equipamento.estado
    equipamento.estado = novo_estado
    equipamento.save(update_fields=["estado"])

    HistoricoEstadoEquipamento.objects.create(
        equipamento=equipamento,
        estado_anterior=estado_anterior,
        estado_novo=novo_estado,
        alterado_por=actor,
        origem=origem,
        motivo=motivo or "",
    )
    return novo_estado


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

    # Fluxo de trabalho permitido: Pendente -> Em Reparação -> Resolvido.
    # Esta regra fica no modelo para ser reutilizada pelas views e pelos templates.
    TRANSICOES_ESTADO = {
        "pendente": ("em_reparacao",),
        "em_reparacao": ("resolvido",),
        "resolvido": (),
        "cancelado": (),
    }

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

    def save(self, *args, **kwargs):
        """Garante a sincronização do equipamento ao criar uma avaria.

        O `save()` é usado pelo admin, pela shell e por qualquer código ORM.
        Como só reagimos à criação (``_state.adding``), as atualizações de
        estado continuam a ser explicitamente sincronizadas pelas views.
        """
        estava_a_ser_criada = self._state.adding
        super().save(*args, **kwargs)

        if estava_a_ser_criada:
            recalcular_estado_equipamento(self.equipamento)

    @property
    def proximos_estados(self):
        """Devolve os estados possíveis a partir do estado atual, já com rótulos.

        Exemplo: uma avaria pendente devolve [("em_reparacao", "Em Reparação")].
        Usamos isto no template para não mostrar transições inválidas.
        """
        rotulos = dict(self.ESTADO_AVARIA_CHOICES)
        return [
            (estado, rotulos[estado])
            for estado in self.TRANSICOES_ESTADO.get(self.estado, ())
        ]


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


class HistoricoEstadoEquipamento(models.Model):
    ORIGEM_CHOICES = (
        ("fluxo", "Fluxo automático"),
        ("manual", "Correção manual"),
    )

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.CASCADE,
        related_name="historico_estados",
    )
    estado_anterior = models.CharField(
        max_length=20, choices=Equipamento.ESTADO_EQUIPAMENTO_CHOICES
    )
    estado_novo = models.CharField(
        max_length=20, choices=Equipamento.ESTADO_EQUIPAMENTO_CHOICES
    )
    alterado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alteracoes_estado_equipamento",
    )
    origem = models.CharField(
        max_length=20, choices=ORIGEM_CHOICES, default="fluxo"
    )
    motivo = models.TextField(blank=True, default="")
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_hora"]

    def __str__(self):
        return (
            f"{self.equipamento.codigo}: {self.estado_anterior} ->"
            f" {self.estado_novo} ({self.get_origem_display()})"
        )
