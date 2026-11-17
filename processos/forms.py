from django import forms
from django.core.exceptions import ValidationError

from .models import AvaliacaoConclusao, Solicitacao


TRANSICOES_PERMITIDAS = {
    Solicitacao.Status.ABERTA: {
        Solicitacao.Status.EM_ANALISE,
        Solicitacao.Status.EM_ATENDIMENTO,
        Solicitacao.Status.CANCELADA,
    },
    Solicitacao.Status.EM_ANALISE: {
        Solicitacao.Status.EM_ATENDIMENTO,
        Solicitacao.Status.CONCLUIDA,
        Solicitacao.Status.CANCELADA,
    },
    Solicitacao.Status.EM_ATENDIMENTO: {
        Solicitacao.Status.EM_ANALISE,
        Solicitacao.Status.CONCLUIDA,
        Solicitacao.Status.CANCELADA,
    },
    Solicitacao.Status.CONCLUIDA: set(),
    Solicitacao.Status.CANCELADA: set(),
}


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = [
            "nome_solicitante",
            "email_solicitante",
            "titulo",
            "categoria",
            "prioridade",
            "descricao",
        ]
        widgets = {
            "nome_solicitante": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex.: Maria Silva"}),
            "email_solicitante": forms.EmailInput(attrs={"class": "form-control", "placeholder": "maria@exemplo.com"}),
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Resumo objetivo da demanda"}),
            "categoria": forms.Select(attrs={"class": "form-control"}),
            "prioridade": forms.Select(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Descreva o contexto, impacto e dados necessários"}
            ),
        }

    def clean_nome_solicitante(self) -> str:
        nome = self.cleaned_data["nome_solicitante"].strip()
        if len(nome) < 3:
            raise ValidationError("Informe o nome completo (mínimo de 3 caracteres).")
        return nome

    def clean_titulo(self) -> str:
        titulo = self.cleaned_data["titulo"].strip()
        if len(titulo) < 5:
            raise ValidationError("O título deve ter pelo menos 5 caracteres.")
        return titulo

    def clean_descricao(self) -> str:
        descricao = self.cleaned_data["descricao"].strip()
        if len(descricao) < 15:
            raise ValidationError("A descrição deve conter ao menos 15 caracteres para análise adequada.")
        return descricao


class ConsultaProtocoloForm(forms.Form):
    protocolo = forms.CharField(
        max_length=24,
        label="Número do protocolo",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ex.: SGPD-2026-A1B2C3"}
        ),
    )

    def clean_protocolo(self) -> str:
        codigo = self.cleaned_data["protocolo"].strip().upper()
        if not codigo.startswith("SGPD-"):
            raise ValidationError("Formato inválido. O protocolo deve iniciar com 'SGPD-'.")
        return codigo


class TramitacaoForm(forms.Form):
    status_novo = forms.ChoiceField(
        choices=Solicitacao.Status.choices,
        label="Novo status",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    observacao = forms.CharField(
        label="Observação da tramitação",
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3, "placeholder": "Registre o parecer ou ação executada"}
        ),
    )

    def __init__(self, *args, solicitacao: Solicitacao, **kwargs):
        self.solicitacao = solicitacao
        super().__init__(*args, **kwargs)
        permitidos = TRANSICOES_PERMITIDAS.get(solicitacao.status, set())
        self.fields["status_novo"].choices = [
            (valor, rotulo)
            for valor, rotulo in Solicitacao.Status.choices
            if valor in permitidos
        ]

    def clean_status_novo(self) -> str:
        novo_status = self.cleaned_data["status_novo"]
        permitidos = TRANSICOES_PERMITIDAS.get(self.solicitacao.status, set())
        if novo_status not in permitidos:
            raise ValidationError("Transição de status não permitida para o estado atual do processo.")
        return novo_status

    def clean_observacao(self) -> str:
        obs = self.cleaned_data["observacao"].strip()
        if len(obs) < 5:
            raise ValidationError("A observação deve ter pelo menos 5 caracteres.")
        return obs


class AvaliacaoConclusaoForm(forms.ModelForm):
    nota = forms.TypedChoiceField(
        coerce=int,
        choices=[(i, f"{i} - {'Muito insatisfeito' if i == 1 else 'Muito satisfeito' if i == 5 else 'Estrelas'}") for i in range(1, 6)],
        label="Nota de atendimento",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = AvaliacaoConclusao
        fields = ["nota", "comentario"]
        widgets = {
            "comentario": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Comentário opcional sobre a resolução"}
            )
        }

    def __init__(self, *args, solicitacao: Solicitacao, **kwargs):
        self.solicitacao = solicitacao
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.solicitacao.status != Solicitacao.Status.CONCLUIDA:
            raise ValidationError("A avaliação só pode ser registrada após a conclusão da solicitação.")
        if hasattr(self.solicitacao, "avaliacao"):
            raise ValidationError("Esta solicitação já possui uma avaliação registrada.")
        return cleaned_data
