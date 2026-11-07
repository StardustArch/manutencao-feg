from django import forms

from .models import Avaria, Equipamento, Intervencao


class AvariaForm(forms.ModelForm):
    """Formulário de reporte de uma avaria."""

    class Meta:
        model = Avaria
        fields = ["descricao", "prioridade"]
        widgets = {
            "descricao": forms.Textarea(
                attrs={"rows": 5, "class": "form-control"}
            ),
            "prioridade": forms.RadioSelect,
        }
        labels = {
            "descricao": "Descrição",
            "prioridade": "Prioridade",
        }


class IntervencaoForm(forms.ModelForm):
    """Registo do trabalho realizado pelo técnico."""

    class Meta:
        model = Intervencao
        fields = ["detalhes_reparacao", "pecas_substituidas"]
        widgets = {
            "detalhes_reparacao": forms.Textarea(
                attrs={"rows": 4, "class": "form-control"}
            ),
            "pecas_substituidas": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
        }
        labels = {
            "detalhes_reparacao": "Detalhes da reparação",
            "pecas_substituidas": "Peças substituídas",
        }


class CorrigirEstadoForm(forms.Form):
    """Correção manual do estado de um equipamento (apenas administradores)."""

    estado = forms.ChoiceField(
        choices=Equipamento.ESTADO_EQUIPAMENTO_CHOICES,
        label="Novo estado",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        label="Motivo",
    )
