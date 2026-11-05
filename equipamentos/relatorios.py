"""Geração dos relatórios em PDF do sistema de manutenção.

Usamos a biblioteca ReportLab porque é leve, pura Python e funciona em
Windows sem depender de motores externos (ao contrário do WeasyPrint, que
precisa do GTK instalado). Os relatórios são construídos em memória e
devolvidos como bytes, pelo que não é necessário configurar MEDIA_ROOT.
"""

import io
from xml.sax.saxutils import escape

from django.db.models import Count, Q
from django.utils import timezone
from django.utils.html import strip_tags

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import Avaria, Equipamento

# Paleta discreta, coerente com os badges usados nos templates.
AZUL = colors.HexColor("#1d4ed8")
CINZA_ESCURO = colors.HexColor("#374151")
CINZA_MEDIO = colors.HexColor("#6b7280")
CINZA_LINHA = colors.HexColor("#d1d5db")
CINZA_FUNDO = colors.HexColor("#f3f4f6")

ESTADOS_EQUIPAMENTO = ("operacional", "avariado", "manutencao", "abatido")
ESTADOS_AVARIA = ("pendente", "em_reparacao", "resolvido", "cancelado")


def _criar_estilos():
    """Cria os estilos tipográficos usados nos dois relatórios."""
    estilos = getSampleStyleSheet()

    estilos.add(
        ParagraphStyle(
            name="TituloRelatorio",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=AZUL,
            alignment=TA_LEFT,
            spaceAfter=2,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="SubtituloRelatorio",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=CINZA_ESCURO,
            spaceAfter=2,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="LegendaRelatorio",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=CINZA_MEDIO,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="SeccaoRelatorio",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=CINZA_ESCURO,
            spaceBefore=4,
            spaceAfter=4,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="CelulaRelatorio",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=CINZA_ESCURO,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="ValorMetrica",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=19,
            textColor=CINZA_ESCURO,
            alignment=TA_LEFT,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="RotuloMetrica",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=CINZA_MEDIO,
        )
    )
    return estilos


def _texto_seguro(valor):
    """Remove HTML e escapa caracteres especiais para o Paragraph do ReportLab."""
    texto = strip_tags(str(valor if valor is not None else "")).strip()
    return escape(texto)


def _celula(valor, estilos):
    return Paragraph(_texto_seguro(valor) or "-", estilos["CelulaRelatorio"])


def _cortar(texto, limite):
    texto = strip_tags(str(texto or "")).strip()
    if len(texto) <= limite:
        return texto
    return texto[: limite - 3].rstrip() + "..."


def _criar_documento(buffer, titulo, paisagem=False):
    pagina = landscape(A4) if paisagem else A4
    documento = SimpleDocTemplate(
        buffer,
        pagesize=pagina,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=24 * mm,
        bottomMargin=18 * mm,
        title=titulo,
        author="Sistema de Manutenção UCM-FEG",
        subject="Relatório gerado automaticamente",
    )
    largura_util = pagina[0] - (30 * mm)
    return documento, largura_util


def _cabecalho_rodape(titulo):
    """Desenha o cabeçalho e o número de página em todas as folhas."""

    def desenhar(canvas, documento):
        canvas.saveState()
        largura, altura = documento.pagesize

        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(CINZA_MEDIO)
        canvas.drawString(15 * mm, altura - 13 * mm, "UCM-FEG · Laboratório de Informática")
        canvas.drawRightString(
            largura - 15 * mm,
            altura - 13 * mm,
            f"{titulo} · {timezone.localdate():%d/%m/%Y}",
        )
        canvas.setStrokeColor(CINZA_LINHA)
        canvas.setLineWidth(0.5)
        canvas.line(15 * mm, altura - 16 * mm, largura - 15 * mm, altura - 16 * mm)

        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            largura / 2,
            10 * mm,
            f"Página {documento.page}",
        )
        canvas.restoreState()

    return desenhar


def _estilo_tabela(linhas_cabecalho=1):
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, linhas_cabecalho - 1), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, linhas_cabecalho - 1), colors.white),
            ("FONTNAME", (0, 0), (-1, linhas_cabecalho - 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, linhas_cabecalho - 1), 8),
            ("FONTNAME", (0, linhas_cabecalho), (-1, -1), "Helvetica"),
            ("GRID", (0, 0), (-1, -1), 0.4, CINZA_LINHA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, linhas_cabecalho), (-1, -1), [colors.white, CINZA_FUNDO]),
        ]
    )


def _tabela_metricas(metricas, largura_util, estilos):
    """Tabela de indicadores: valores na primeira linha, rótulos na segunda."""
    valores = [
        Paragraph(str(valor), estilos["ValorMetrica"]) for _, valor in metricas
    ]
    rotulos = [
        Paragraph(_texto_seguro(rotulo), estilos["RotuloMetrica"])
        for rotulo, _ in metricas
    ]

    tabela = Table(
        [valores, rotulos],
        colWidths=[largura_util / len(metricas)] * len(metricas),
    )
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CINZA_FUNDO),
                ("BOX", (0, 0), (-1, -1), 0.4, CINZA_LINHA),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, CINZA_LINHA),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
            ]
        )
    )
    return tabela


def _gerar_inventario():
    buffer = io.BytesIO()
    titulo = "Relatório de Inventário"
    documento, largura_util = _criar_documento(buffer, titulo)
    estilos = _criar_estilos()

    equipamentos = list(
        Equipamento.objects.annotate(
            avarias_abertas=Count(
                "avarias",
                filter=Q(avarias__estado__in=["pendente", "em_reparacao"]),
            )
        ).order_by("codigo")
    )

    contagem = {estado: 0 for estado in ESTADOS_EQUIPAMENTO}
    for equipamento in equipamentos:
        if equipamento.estado in contagem:
            contagem[equipamento.estado] += 1

    elementos = [
        Paragraph(titulo, estilos["TituloRelatorio"]),
        Paragraph(
            "Laboratório de Informática da Universidade Católica de Moçambique - FEG",
            estilos["SubtituloRelatorio"],
        ),
        Paragraph(
            f"Gerado a {timezone.localtime():%d/%m/%Y} às {timezone.localtime():%H:%M}",
            estilos["LegendaRelatorio"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Resumo do inventário", estilos["SeccaoRelatorio"]),
        _tabela_metricas(
            [
                ("Total", len(equipamentos)),
                ("Operacionais", contagem["operacional"]),
                ("Avariados", contagem["avariado"]),
                ("Em manutenção", contagem["manutencao"]),
                ("Abatidos", contagem["abatido"]),
            ],
            largura_util,
            estilos,
        ),
        Spacer(1, 7 * mm),
        Paragraph("Equipamentos registados", estilos["SeccaoRelatorio"]),
    ]

    cabecalho = [
        "Código",
        "Tipo",
        "Marca / Modelo",
        "Localização",
        "Estado",
        "Avarias abertas",
    ]
    linhas = [cabecalho]
    for equipamento in equipamentos:
        linhas.append(
            [
                _celula(equipamento.codigo, estilos),
                _celula(equipamento.get_tipo_display(), estilos),
                _celula(equipamento.marca_modelo, estilos),
                _celula(equipamento.localizacao, estilos),
                _celula(equipamento.get_estado_display(), estilos),
                _celula(equipamento.avarias_abertas, estilos),
            ]
        )

    if equipamentos:
        tabela = Table(
            linhas,
            colWidths=[25 * mm, 25 * mm, 43 * mm, 40 * mm, 25 * mm, 22 * mm],
            repeatRows=1,
        )
        tabela.setStyle(_estilo_tabela())
        elementos.append(tabela)
    else:
        elementos.append(
            Paragraph(
                "Ainda não existem equipamentos registados no inventário.",
                estilos["SubtituloRelatorio"],
            )
        )

    elementos.extend(
        [
            Spacer(1, 6 * mm),
            Paragraph(
                "Documento gerado automaticamente pelo Sistema de Gestão de "
                "Manutenção do Laboratório de Informática da UCM-FEG.",
                estilos["LegendaRelatorio"],
            ),
        ]
    )

    documento.build(
        elementos,
        onFirstPage=_cabecalho_rodape(titulo),
        onLaterPages=_cabecalho_rodape(titulo),
    )
    return buffer.getvalue()


def _gerar_avarias():
    buffer = io.BytesIO()
    titulo = "Relatório de Avarias"
    documento, largura_util = _criar_documento(buffer, titulo, paisagem=True)
    estilos = _criar_estilos()

    avarias = list(
        Avaria.objects.select_related("equipamento", "tecnico_atribuido").order_by(
            "-data_registo"
        )
    )

    contagem = {estado: 0 for estado in ESTADOS_AVARIA}
    for avaria in avarias:
        if avaria.estado in contagem:
            contagem[avaria.estado] += 1

    elementos = [
        Paragraph(titulo, estilos["TituloRelatorio"]),
        Paragraph(
            "Laboratório de Informática da Universidade Católica de Moçambique - FEG",
            estilos["SubtituloRelatorio"],
        ),
        Paragraph(
            f"Gerado a {timezone.localtime():%d/%m/%Y} às {timezone.localtime():%H:%M}",
            estilos["LegendaRelatorio"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Resumo das avarias", estilos["SeccaoRelatorio"]),
        _tabela_metricas(
            [
                ("Total", len(avarias)),
                ("Pendentes", contagem["pendente"]),
                ("Em reparação", contagem["em_reparacao"]),
                ("Resolvidas", contagem["resolvido"]),
                ("Canceladas", contagem["cancelado"]),
            ],
            largura_util,
            estilos,
        ),
        Spacer(1, 6 * mm),
        Paragraph("Registo de avarias", estilos["SeccaoRelatorio"]),
    ]

    cabecalho = [
        "#",
        "Equipamento",
        "Descrição",
        "Prioridade",
        "Estado",
        "Técnico",
        "Registo",
    ]
    linhas = [cabecalho]
    for avaria in avarias:
        linhas.append(
            [
                _celula(avaria.pk, estilos),
                _celula(
                    f"{avaria.equipamento.codigo} - {avaria.equipamento.marca_modelo}",
                    estilos,
                ),
                _celula(_cortar(avaria.descricao, 170), estilos),
                _celula(avaria.get_prioridade_display(), estilos),
                _celula(avaria.get_estado_display(), estilos),
                _celula(
                    avaria.tecnico_atribuido.username
                    if avaria.tecnico_atribuido
                    else "Não atribuída",
                    estilos,
                ),
                _celula(
                    timezone.localtime(avaria.data_registo).strftime("%d/%m/%Y %H:%M"),
                    estilos,
                ),
            ]
        )

    if avarias:
        tabela = Table(
            linhas,
            colWidths=[
                11 * mm,
                42 * mm,
                82 * mm,
                21 * mm,
                28 * mm,
                40 * mm,
                32 * mm,
            ],
            repeatRows=1,
        )
        tabela.setStyle(_estilo_tabela())
        elementos.append(tabela)
    else:
        elementos.append(
            Paragraph(
                "Ainda não existem avarias registadas.",
                estilos["SubtituloRelatorio"],
            )
        )

    elementos.extend(
        [
            Spacer(1, 6 * mm),
            Paragraph(
                "Documento gerado automaticamente pelo Sistema de Gestão de "
                "Manutenção do Laboratório de Informática da UCM-FEG.",
                estilos["LegendaRelatorio"],
            ),
        ]
    )

    documento.build(
        elementos,
        onFirstPage=_cabecalho_rodape(titulo),
        onLaterPages=_cabecalho_rodape(titulo),
    )
    return buffer.getvalue()


def gerar_relatorio_pdf(tipo="inventario"):
    """Devolve o conteúdo binário do relatório pedido.

    `tipo` aceita "inventario" (por omissão) ou "avarias".
    """
    if tipo == "avarias":
        return _gerar_avarias()
    return _gerar_inventario()
