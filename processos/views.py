from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AvaliacaoConclusaoForm,
    ConsultaProtocoloForm,
    SolicitacaoForm,
    TramitacaoForm,
)
from .models import HistoricoTramitacao, Solicitacao


def inicio(request):
    """Tela 1 (RF01 / RF02): Abertura de nova solicitação e consulta rápida por protocolo."""
    solicitacao_form = SolicitacaoForm()
    consulta_form = ConsultaProtocoloForm()

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "criar_solicitacao":
            solicitacao_form = SolicitacaoForm(request.POST)
            if solicitacao_form.is_valid():
                with transaction.atomic():
                    solicitacao = solicitacao_form.save(commit=False)
                    if request.user.is_authenticated:
                        solicitacao.solicitante = request.user
                    solicitacao.save()

                    HistoricoTramitacao.objects.create(
                        solicitacao=solicitacao,
                        autor=request.user if request.user.is_authenticated else None,
                        status_anterior="",
                        status_novo=Solicitacao.Status.ABERTA,
                        observacao="Solicitação registrada no sistema e encaminhada para triagem.",
                    )
                messages.success(
                    request,
                    f"Solicitação registrada com sucesso. Protocolo gerado: {solicitacao.protocolo}.",
                )
                return redirect("processos:protocolo_detalhe", protocolo=solicitacao.protocolo)

        elif acao == "consultar_protocolo":
            consulta_form = ConsultaProtocoloForm(request.POST)
            if consulta_form.is_valid():
                codigo = consulta_form.cleaned_data["protocolo"]
                if Solicitacao.objects.filter(protocolo=codigo).exists():
                    return redirect("processos:protocolo_detalhe", protocolo=codigo)
                consulta_form.add_error("protocolo", f"Nenhum processo encontrado para o protocolo {codigo}.")

    return render(
        request,
        "processos/inicio.html",
        {
            "solicitacao_form": solicitacao_form,
            "consulta_form": consulta_form,
        },
    )


def painel(request):
    """Tela 2 (RF03): Painel de acompanhamento e filtragem de solicitações."""
    queryset = Solicitacao.objects.all()

    status_filtro = request.GET.get("status", "").strip()
    categoria_filtro = request.GET.get("categoria", "").strip()
    prioridade_filtro = request.GET.get("prioridade", "").strip()
    busca = request.GET.get("q", "").strip()

    if status_filtro:
        queryset = queryset.filter(status=status_filtro)
    if categoria_filtro:
        queryset = queryset.filter(categoria=categoria_filtro)
    if prioridade_filtro:
        queryset = queryset.filter(prioridade=prioridade_filtro)
    if busca:
        queryset = queryset.filter(
            Q(protocolo__icontains=busca)
            | Q(titulo__icontains=busca)
            | Q(nome_solicitante__icontains=busca)
        )

    todas = Solicitacao.objects.all()
    metricas = {
        "total": todas.count(),
        "abertas": todas.filter(status=Solicitacao.Status.ABERTA).count(),
        "em_andamento": todas.filter(
            status__in=[Solicitacao.Status.EM_ANALISE, Solicitacao.Status.EM_ATENDIMENTO]
        ).count(),
        "concluidas": todas.filter(status=Solicitacao.Status.CONCLUIDA).count(),
    }

    return render(
        request,
        "processos/painel.html",
        {
            "solicitacoes": queryset,
            "metricas": metricas,
            "status_choices": Solicitacao.Status.choices,
            "categoria_choices": Solicitacao.Categoria.choices,
            "prioridade_choices": Solicitacao.Prioridade.choices,
            "filtros": {
                "status": status_filtro,
                "categoria": categoria_filtro,
                "prioridade": prioridade_filtro,
                "q": busca,
            },
        },
    )


def protocolo_detalhe(request, protocolo: str):
    """Tela 3 (RF02 / RF04): Detalhamento, tramitação e avaliação de conclusão."""
    solicitacao = get_object_or_404(Solicitacao, protocolo=protocolo.upper())
    historico = solicitacao.historico.select_related("autor").all()

    tramitacao_form = TramitacaoForm(solicitacao=solicitacao)
    avaliacao_form = AvaliacaoConclusaoForm(solicitacao=solicitacao)

    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "tramitar":
            tramitacao_form = TramitacaoForm(request.POST, solicitacao=solicitacao)
            if tramitacao_form.is_valid():
                with transaction.atomic():
                    status_anterior = solicitacao.status
                    solicitacao.status = tramitacao_form.cleaned_data["status_novo"]
                    solicitacao.save()

                    HistoricoTramitacao.objects.create(
                        solicitacao=solicitacao,
                        autor=request.user if request.user.is_authenticated else None,
                        status_anterior=status_anterior,
                        status_novo=solicitacao.status,
                        observacao=tramitacao_form.cleaned_data["observacao"],
                    )
                messages.success(request, "Tramitação registrada com sucesso.")
                return redirect("processos:protocolo_detalhe", protocolo=solicitacao.protocolo)

        elif acao == "avaliar":
            avaliacao_form = AvaliacaoConclusaoForm(request.POST, solicitacao=solicitacao)
            if avaliacao_form.is_valid():
                avaliacao = avaliacao_form.save(commit=False)
                avaliacao.solicitacao = solicitacao
                avaliacao.save()
                messages.success(request, "Avaliação de conclusão registrada. Obrigado pelo retorno.")
                return redirect("processos:protocolo_detalhe", protocolo=solicitacao.protocolo)

    pode_tramitar = bool(tramitacao_form.fields["status_novo"].choices)
    pode_avaliar = (
        solicitacao.status == Solicitacao.Status.CONCLUIDA
        and not hasattr(solicitacao, "avaliacao")
    )

    return render(
        request,
        "processos/protocolo_detalhe.html",
        {
            "solicitacao": solicitacao,
            "historico": historico,
            "tramitacao_form": tramitacao_form,
            "avaliacao_form": avaliacao_form,
            "pode_tramitar": pode_tramitar,
            "pode_avaliar": pode_avaliar,
        },
    )
