import io
from functools import wraps

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .forms import AvariaForm, CorrigirEstadoForm, IntervencaoForm
from .models import (
    Avaria,
    Equipamento,
    Intervencao,
    recalcular_estado_equipamento,
)
from .relatorios import gerar_relatorio_pdf

# ---------------------------------------------------------------------------
# Permissões
# ---------------------------------------------------------------------------


def _e_tecnico_ou_admin(user):
    """Indica se o utilizador pertence à equipa técnica ou à administração."""
    perfil = getattr(user, "perfil", None)
    return user.is_superuser or (
        perfil and perfil.papel in {"tecnico", "admin"}
    )


def tecnico_ou_admin_required(view_func):
    """Permite o acesso apenas a técnicos, administradores ou superutilizadores.

    É um decorador personalizado: junta o `login_required` (obriga a sessão
    iniciada) com a verificação do papel guardado no modelo `Perfil`.
    """

    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not _e_tecnico_ou_admin(request.user):
            raise PermissionDenied(
                "Apenas técnicos e administradores podem aceder a esta área."
            )

        return view_func(request, *args, **kwargs)

    return _wrapped


def _e_admin(user):
    """Indica se o utilizador tem privilégios de administração."""
    perfil = getattr(user, "perfil", None)
    return user.is_superuser or (perfil and perfil.papel == "admin")


def admin_required(view_func):
    """Permite o acesso apenas a administradores ou superutilizadores."""

    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not _e_admin(request.user):
            raise PermissionDenied(
                "Apenas administradores podem aceder a esta área."
            )

        return view_func(request, *args, **kwargs)

    return _wrapped


# ---------------------------------------------------------------------------
# Contexto e respostas auxiliares
# ---------------------------------------------------------------------------


def url_absoluta(request, path):
    """Constrói um URL absoluto usando SITE_URL, se estiver definido.

    Sem SITE_URL, mantém o comportamento anterior e recorre ao host do pedido.
    """
    base = getattr(settings, "SITE_URL", "").rstrip("/")
    return f"{base}{path}" if base else request.build_absolute_uri(path)


def _contexto_lista_avarias(request):
    """Prepara todos os dados usados na listagem e no partial HTMX."""
    estado = request.GET.get("estado", "").strip()
    prioridade = request.GET.get("prioridade", "").strip()

    estados_validos = dict(Avaria.ESTADO_AVARIA_CHOICES)
    prioridades_validas = dict(Avaria.PRIORIDADE_CHOICES)

    # Ignora valores manipulados no URL (?estado=xyz), por segurança.
    if estado not in estados_validos:
        estado = ""
    if prioridade not in prioridades_validas:
        prioridade = ""

    avarias = Avaria.objects.select_related(
        "equipamento",
        "reportado_por",
        "tecnico_atribuido",
    ).annotate(
        # Ordena por gravidade: urgente -> alta -> média -> baixa.
        ordem_prioridade=Case(
            When(prioridade="urgente", then=Value(0)),
            When(prioridade="alta", then=Value(1)),
            When(prioridade="media", then=Value(2)),
            When(prioridade="baixa", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    if estado:
        avarias = avarias.filter(estado=estado)

    if prioridade:
        avarias = avarias.filter(prioridade=prioridade)

    avarias = avarias.order_by("ordem_prioridade", "-data_registo")

    resumo = {
        "pendentes": Avaria.objects.filter(estado="pendente").count(),
        "em_reparacao": Avaria.objects.filter(estado="em_reparacao").count(),
        "resolvidas": Avaria.objects.filter(estado="resolvido").count(),
        "urgentes_abertas": Avaria.objects.filter(
            estado__in=["pendente", "em_reparacao"],
            prioridade="urgente",
        ).count(),
    }

    return {
        "avarias": avarias,
        "estados": Avaria.ESTADO_AVARIA_CHOICES,
        "prioridades": Avaria.PRIORIDADE_CHOICES,
        "estado_atual": estado,
        "prioridade_atual": prioridade,
        "estado_atual_display": estados_validos.get(estado, ""),
        "prioridade_atual_display": prioridades_validas.get(prioridade, ""),
        "resumo": resumo,
        # Mantém os filtros ativos nos URLs das ações HTMX.
        "filtros_querystring": request.GET.urlencode(),
        "e_admin": _e_admin(request.user),
    }


def _render_lista_avarias(request):
    """Devolve apenas o bloco que o HTMX substitui na página."""
    return render(
        request,
        "equipamentos/partials/_avarias_conteudo.html",
        _contexto_lista_avarias(request),
    )


def _redirecionar_para_lista(request):
    """Fallback para pedidos normais (sem JavaScript/HTMX)."""
    url = reverse("equipamentos:avarias_lista")
    query = request.GET.urlencode()
    return redirect(f"{url}?{query}" if query else url)


def _responder_acao(request):
    """Responde em HTML parcial para HTMX ou redireciona no modo tradicional."""
    if request.headers.get("HX-Request"):
        return _render_lista_avarias(request)
    return _redirecionar_para_lista(request)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


@tecnico_ou_admin_required
def avarias_lista(request):
    """Listagem de avarias com filtros por estado e prioridade."""
    contexto = _contexto_lista_avarias(request)

    # O HTMX só precisa do fragmento, não da página HTML completa.
    if request.headers.get("HX-Request"):
        return render(
            request,
            "equipamentos/partials/_avarias_conteudo.html",
            contexto,
        )

    return render(request, "equipamentos/avarias_lista.html", contexto)


@tecnico_ou_admin_required
@require_POST
def assumir_avaria(request, pk):
    """Atribui a avaria ao técnico autenticado e inicia a reparação."""
    avaria = get_object_or_404(
        Avaria.objects.select_related("equipamento", "tecnico_atribuido"),
        pk=pk,
    )

    if avaria.estado in {"resolvido", "cancelado"}:
        messages.error(request, "Esta avaria já está fechada e não pode ser assumida.")

    elif avaria.tecnico_atribuido and avaria.tecnico_atribuido != request.user:
        messages.error(
            request,
            f"Esta avaria já está atribuída a {avaria.tecnico_atribuido.username}.",
        )

    elif avaria.tecnico_atribuido == request.user:
        messages.info(request, "Esta avaria já está atribuída a ti.")

    else:
        with transaction.atomic():
            avaria.tecnico_atribuido = request.user

            # Ao assumir uma avaria pendente, ela entra automaticamente em reparação.
            if avaria.estado == "pendente":
                avaria.estado = "em_reparacao"

            avaria.save()
            recalcular_estado_equipamento(
                avaria.equipamento,
                actor=request.user,
            )

        messages.success(
            request,
            f"Avaria #{avaria.pk} assumida. Bom trabalho na reparação!",
        )

    return _responder_acao(request)


@tecnico_ou_admin_required
@require_POST
def alterar_estado_avaria(request, pk):
    """Altera o estado de uma avaria respeitando as transições permitidas."""
    avaria = get_object_or_404(
        Avaria.objects.select_related("equipamento", "tecnico_atribuido"),
        pk=pk,
    )
    novo_estado = request.POST.get("estado", "").strip()

    estados_validos = dict(Avaria.ESTADO_AVARIA_CHOICES)

    if novo_estado not in estados_validos:
        messages.error(request, "Estado inválido.")
        return _responder_acao(request)

    if novo_estado not in Avaria.TRANSICOES_ESTADO.get(avaria.estado, ()):
        messages.error(
            request,
            (
                f"Transição inválida: não é possível passar de "
                f"{avaria.get_estado_display()} para "
                f"{estados_validos[novo_estado]}."
            ),
        )
        return _responder_acao(request)

    # Um técnico só pode mexer em avarias que lhe estão atribuídas.
    # O administrador pode gerir qualquer avaria.
    if not _e_admin(request.user):
        if (
            avaria.tecnico_atribuido
            and avaria.tecnico_atribuido != request.user
        ):
            messages.error(
                request,
                "Esta avaria está atribuída a outro técnico.",
            )
            return _responder_acao(request)

        if novo_estado == "resolvido" and not avaria.tecnico_atribuido:
            messages.error(
                request,
                "Atribui primeiro a avaria a um técnico antes de a resolver.",
            )
            return _responder_acao(request)

    # Se um técnico iniciar a reparação de uma avaria ainda sem responsável,
    # a atribuição é feita automaticamente.
    with transaction.atomic():
        if novo_estado == "em_reparacao" and not avaria.tecnico_atribuido:
            avaria.tecnico_atribuido = request.user

        avaria.estado = novo_estado
        avaria.save()
        recalcular_estado_equipamento(
            avaria.equipamento,
            actor=request.user,
        )

    messages.success(
        request,
        f"Avaria #{avaria.pk} atualizada para {avaria.get_estado_display()}.",
    )
    return _responder_acao(request)


@login_required
def reportar_avaria(request):
    """Permite a qualquer utilizador autenticado reportar uma avaria."""
    if request.method == "POST":
        form = AvariaForm(request.POST)
        equipamento_id = request.POST.get("equipamento", "").strip()
        equipamento = (
            Equipamento.objects.filter(pk=equipamento_id).first()
            if equipamento_id.isdigit()
            else None
        )

        if equipamento is None:
            form.add_error(None, "Selecione um equipamento válido.")

        elif equipamento.estado == "abatido":
            form.add_error(
                None,
                "Não é possível reportar avarias para um equipamento abatido.",
            )

        if not form.errors:
            avaria = form.save(commit=False)
            avaria.equipamento = equipamento
            avaria.reportado_por = request.user
            avaria.estado = "pendente"
            avaria.save()

            messages.success(
                request,
                f"Avaria #{avaria.pk} registada com sucesso.",
            )
            return redirect("equipamentos:minhas_avarias")

    else:
        form = AvariaForm()

    contexto = {
        "form": form,
        "equipamento": None,
        "equipamentos": Equipamento.objects.exclude(estado="abatido").order_by(
            "codigo"
        ),
    }
    return render(request, "equipamentos/reportar_avaria.html", contexto)


@login_required
def reportar_avaria_equipamento(request, pk):
    """Reporta uma avaria para o equipamento identificado no URL."""
    equipamento = get_object_or_404(Equipamento, pk=pk)

    if equipamento.estado == "abatido":
        messages.error(
            request,
            "Não é possível reportar avarias para um equipamento abatido.",
        )
        return redirect(
            "equipamentos:equipamento_detalhe",
            pk=equipamento.pk,
        )

    if request.method == "POST":
        form = AvariaForm(request.POST)
        equipamento_id = request.POST.get("equipamento", "").strip()

        if equipamento_id and equipamento_id != str(equipamento.pk):
            form.add_error(
                None,
                "Os dados do equipamento não correspondem ao pedido.",
            )

        if not form.errors:
            avaria = form.save(commit=False)
            avaria.equipamento = equipamento
            avaria.reportado_por = request.user
            avaria.estado = "pendente"
            avaria.save()

            messages.success(
                request,
                f"Avaria #{avaria.pk} registada para {equipamento.codigo}.",
            )
            return redirect("equipamentos:minhas_avarias")

    else:
        form = AvariaForm()

    contexto = {
        "form": form,
        "equipamento": equipamento,
    }
    return render(request, "equipamentos/reportar_avaria.html", contexto)


@login_required
def minhas_avarias(request):
    """Lista as avarias reportadas pelo utilizador autenticado."""
    avarias = (
        Avaria.objects.filter(reportado_por=request.user)
        .select_related("equipamento", "tecnico_atribuido")
        .order_by("-data_registo")
    )
    return render(
        request,
        "equipamentos/minhas_avarias.html",
        {"avarias": avarias},
    )


@login_required
def avaria_detalhe(request, pk):
    """Detalhe de uma avaria, com as intervenções já realizadas."""
    avaria = get_object_or_404(
        Avaria.objects.select_related(
            "equipamento",
            "reportado_por",
            "tecnico_atribuido",
        ),
        pk=pk,
    )
    intervencoes = avaria.intervencoes.select_related("tecnico").order_by(
        "-data_intervencao"
    )

    pode_registar_intervencao = _e_admin(request.user) or (
        avaria.tecnico_atribuido == request.user
    )
    intervencao_form = (
        IntervencaoForm() if pode_registar_intervencao else None
    )

    contexto = {
        "avaria": avaria,
        "intervencoes": intervencoes,
        "pode_registar_intervencao": pode_registar_intervencao,
        "intervencao_form": intervencao_form,
        "e_admin": _e_admin(request.user),
    }
    return render(request, "equipamentos/avaria_detalhe.html", contexto)


@tecnico_ou_admin_required
@require_POST
def registar_intervencao(request, pk):
    """Regista uma intervenção do técnico autenticado numa avaria."""
    avaria = get_object_or_404(Avaria, pk=pk)
    form = IntervencaoForm(request.POST)

    if form.is_valid():
        intervencao = form.save(commit=False)
        intervencao.avaria = avaria
        intervencao.tecnico = request.user
        intervencao.save()

        messages.success(
            request,
            f"Intervenção registada na avaria #{avaria.pk}.",
        )
    else:
        messages.error(
            request,
            "Não foi possível registar a intervenção. Verifica os dados.",
        )

    return redirect("equipamentos:avaria_detalhe", pk=avaria.pk)


@admin_required
@require_POST
def corrigir_estado(request, pk):
    """Correção manual do estado de um equipamento, com motivo obrigatório."""
    equipamento = get_object_or_404(Equipamento, pk=pk)
    form = CorrigirEstadoForm(request.POST)

    if form.is_valid():
        with transaction.atomic():
            recalcular_estado_equipamento(
                equipamento,
                actor=request.user,
                origem="manual",
                motivo=form.cleaned_data["motivo"],
                estado_manual=form.cleaned_data["estado"],
            )

        messages.success(
            request,
            f"Estado de {equipamento.codigo} corrigido para"
            f" {equipamento.get_estado_display()}.",
        )
    else:
        messages.error(
            request,
            "Não foi possível corrigir o estado. O motivo é obrigatório.",
        )

    return redirect(
        "equipamentos:equipamento_detalhe",
        pk=equipamento.pk,
    )


@tecnico_ou_admin_required
def dashboard_metricas(request):
    """Dashboard com totais e distribuição de equipamentos e avarias por estado.

    As contagens são calculadas com `values(...).annotate(Count(...))`, que
    equivale a um `GROUP BY estado` em SQL. Assim evitamos uma consulta por
    cada estado e mantemos a view eficiente.
    """
    estados_equipamento = dict(Equipamento.ESTADO_EQUIPAMENTO_CHOICES)
    estados_avaria = dict(Avaria.ESTADO_AVARIA_CHOICES)

    # Inicializa todos os estados com zero, para os gráficos nunca ficarem
    # com posições em falta quando ainda não existem registos.
    contagem_equipamentos = {estado: 0 for estado in estados_equipamento}
    for linha in Equipamento.objects.values("estado").annotate(total=Count("id")):
        if linha["estado"] in contagem_equipamentos:
            contagem_equipamentos[linha["estado"]] = linha["total"]

    contagem_avarias = {estado: 0 for estado in estados_avaria}
    for linha in Avaria.objects.values("estado").annotate(total=Count("id")):
        if linha["estado"] in contagem_avarias:
            contagem_avarias[linha["estado"]] = linha["total"]

    # O gráfico de barras mostra apenas os três estados pedidos no Passo 6.
    estados_avaria_grafico = ("pendente", "em_reparacao", "resolvido")

    contexto = {
        "total_equipamentos": Equipamento.objects.count(),
        "total_avarias": Avaria.objects.count(),
        "equipamentos_por_estado": contagem_equipamentos,
        "avarias_por_estado": contagem_avarias,
        "avarias_abertas": (
            contagem_avarias["pendente"] + contagem_avarias["em_reparacao"]
        ),
        # Estruturas preparadas para o Chart.js. O template usa `json_script`
        # para as injetar no JavaScript de forma segura (sem concatenar HTML).
        "grafico_equipamentos": {
            "labels": [
                estados_equipamento[estado] for estado in estados_equipamento
            ],
            "valores": [
                contagem_equipamentos[estado] for estado in estados_equipamento
            ],
        },
        "grafico_avarias": {
            "labels": [
                estados_avaria[estado] for estado in estados_avaria_grafico
            ],
            "valores": [
                contagem_avarias[estado] for estado in estados_avaria_grafico
            ],
        },
        "e_admin": _e_admin(request.user),
    }

    return render(request, "equipamentos/dashboard.html", contexto)


# ---------------------------------------------------------------------------
# Inventário, QR Codes e Relatórios PDF (Passo 7)
# ---------------------------------------------------------------------------


@login_required
def equipamentos_lista(request):
    """Inventário com pesquisa, filtro por estado e miniatura do QR code."""
    pesquisa = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()

    estados_validos = dict(Equipamento.ESTADO_EQUIPAMENTO_CHOICES)
    if estado not in estados_validos:
        estado = ""

    equipamentos = Equipamento.objects.annotate(
        avarias_abertas=Count(
            "avarias",
            filter=Q(avarias__estado__in=["pendente", "em_reparacao"]),
        )
    )

    if pesquisa:
        equipamentos = equipamentos.filter(
            Q(codigo__icontains=pesquisa)
            | Q(marca_modelo__icontains=pesquisa)
            | Q(localizacao__icontains=pesquisa)
        )

    if estado:
        equipamentos = equipamentos.filter(estado=estado)

    contexto = {
        "equipamentos": equipamentos.order_by("codigo"),
        "estados": Equipamento.ESTADO_EQUIPAMENTO_CHOICES,
        "estado_atual": estado,
        "estado_atual_display": estados_validos.get(estado, ""),
        "pesquisa": pesquisa,
        "e_tecnico_ou_admin": _e_tecnico_ou_admin(request.user),
    }
    return render(request, "equipamentos/equipamentos_lista.html", contexto)


@tecnico_ou_admin_required
def etiquetas(request):
    """Folha A4 com etiquetas QR dos equipamentos, pronta a imprimir."""
    estado = request.GET.get("estado", "").strip()
    estados_validos = dict(Equipamento.ESTADO_EQUIPAMENTO_CHOICES)

    if estado not in estados_validos:
        estado = ""

    equipamentos = Equipamento.objects.order_by("codigo")
    if estado:
        equipamentos = equipamentos.filter(estado=estado)

    # Cada folha A4 tem 3 colunas x 8 linhas = 24 etiquetas.
    tamanho_pagina = 24
    lista_equipamentos = list(equipamentos)
    paginas = [
        lista_equipamentos[inicio : inicio + tamanho_pagina]
        for inicio in range(0, len(lista_equipamentos), tamanho_pagina)
    ]

    contexto = {
        "paginas": paginas,
        "total_equipamentos": len(lista_equipamentos),
        "estados": Equipamento.ESTADO_EQUIPAMENTO_CHOICES,
        "estado_atual": estado,
        "estado_atual_display": estados_validos.get(estado, ""),
    }
    return render(request, "equipamentos/etiquetas.html", contexto)


@login_required
def equipamento_detalhe(request, pk):
    """Ficha do equipamento com os dados, QR code e histórico de avarias."""
    equipamento = get_object_or_404(Equipamento, pk=pk)
    avarias = equipamento.avarias.select_related(
        "reportado_por",
        "tecnico_atribuido",
    ).order_by("-data_registo")
    e_admin = _e_admin(request.user)

    contexto = {
        "equipamento": equipamento,
        "avarias": avarias,
        "historico_estados": equipamento.historico_estados.select_related(
            "alterado_por"
        ),
        "corrigir_estado_form": (
            CorrigirEstadoForm(initial={"estado": equipamento.estado})
            if e_admin
            else None
        ),
        "e_admin": e_admin,
        "e_tecnico_ou_admin": _e_tecnico_ou_admin(request.user),
    }
    return render(request, "equipamentos/equipamento_detalhe.html", contexto)


@login_required
def equipamento_qrcode(request, pk):
    """Gera o QR code PNG do equipamento, sem guardar ficheiros no disco.

    O QR contém o URL absoluto da página de reporte de avaria do equipamento.
    O URL absoluto é importante para que possa ser lido por um telemóvel na
    rede local (ex.: http://192.168.1.10:8000/equipamentos/3/reportar/).
    """
    equipamento = get_object_or_404(Equipamento, pk=pk)

    url_equipamento = url_absoluta(
        request,
        reverse(
            "equipamentos:reportar_avaria_equipamento",
            kwargs={"pk": equipamento.pk},
        ),
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url_equipamento)
    qr.make(fit=True)

    imagem = qr.make_image(fill_color="black", back_color="white")
    imagem = imagem.get_image().convert("RGB")

    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")

    codigo_ficheiro = slugify(equipamento.codigo) or f"equipamento-{equipamento.pk}"
    resposta = HttpResponse(buffer.getvalue(), content_type="image/png")
    resposta["Content-Disposition"] = (
        f'inline; filename="qrcode-{codigo_ficheiro}.png"'
    )
    # O URL pode mudar entre pedidos (host/porta), por isso não é público.
    resposta["Cache-Control"] = "private, max-age=3600"
    return resposta


@tecnico_ou_admin_required
def relatorio_pdf(request):
    """Exporta o inventário ou as avarias num relatório PDF.

    Exemplos:
        /equipamentos/relatorio/pdf/
        /equipamentos/relatorio/pdf/?tipo=avarias

    O ReportLab gera o documento em memória, pelo que não é necessário
    configurar uma pasta de media nem instalar bibliotecas de sistema.
    """
    tipo = request.GET.get("tipo", "inventario").strip().lower()
    if tipo not in {"inventario", "avarias"}:
        tipo = "inventario"

    conteudo = gerar_relatorio_pdf(tipo)
    nome_ficheiro = f"relatorio_{tipo}.pdf"

    resposta = HttpResponse(conteudo, content_type="application/pdf")
    resposta["Content-Disposition"] = (
        f'attachment; filename="{nome_ficheiro}"'
    )
    return resposta
