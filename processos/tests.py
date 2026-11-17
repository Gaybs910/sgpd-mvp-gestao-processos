import pytest
from django.urls import reverse

from processos.forms import AvaliacaoConclusaoForm, SolicitacaoForm, TramitacaoForm
from processos.models import AvaliacaoConclusao, HistoricoTramitacao, Solicitacao


@pytest.mark.django_db
def test_geracao_automatica_de_protocolo_e_str():
    solicitacao = Solicitacao.objects.create(
        titulo="Solicitação de acesso ao sistema",
        descricao="Necessário liberar acesso ao módulo financeiro para auditoria.",
        nome_solicitante="Ana Pereira",
        email_solicitante="ana@exemplo.com",
    )
    assert solicitacao.protocolo.startswith("SGPD-")
    assert solicitacao.status == Solicitacao.Status.ABERTA
    assert solicitacao.protocolo in str(solicitacao)


@pytest.mark.django_db
def test_validacao_server_side_formulario_solicitacao():
    form = SolicitacaoForm(
        data={
            "nome_solicitante": "Al",
            "email_solicitante": "email-invalido",
            "titulo": "Oi",
            "categoria": Solicitacao.Categoria.TI,
            "prioridade": Solicitacao.Prioridade.MEDIA,
            "descricao": "Curta",
        }
    )
    assert not form.is_valid()
    assert "nome_solicitante" in form.errors
    assert "email_solicitante" in form.errors
    assert "titulo" in form.errors
    assert "descricao" in form.errors


@pytest.mark.django_db
def test_fluxo_completo_rf01_rf02_rf03_rf04(client):
    # RF01: Criação pela tela inicial
    resp = client.post(
        reverse("processos:inicio"),
        data={
            "acao": "criar_solicitacao",
            "nome_solicitante": "Carlos Eduardo",
            "email_solicitante": "carlos@exemplo.com",
            "titulo": "Atualização de cadastro corporativo",
            "categoria": Solicitacao.Categoria.ADMINISTRATIVO,
            "prioridade": Solicitacao.Prioridade.ALTA,
            "descricao": "Solicito atualização dos dados cadastrais do departamento.",
        },
    )
    assert resp.status_code == 302
    solicitacao = Solicitacao.objects.get()
    assert HistoricoTramitacao.objects.filter(solicitacao=solicitacao).count() == 1

    # RF03: Listagem e filtro no painel
    painel_resp = client.get(reverse("processos:painel"), {"status": Solicitacao.Status.ABERTA})
    assert painel_resp.status_code == 200
    assert solicitacao.protocolo in painel_resp.content.decode("utf-8")

    # RF02: Tramitação para EM_ANALISE e depois CONCLUIDA
    detalhe_url = reverse("processos:protocolo_detalhe", args=[solicitacao.protocolo])
    client.post(
        detalhe_url,
        data={
            "acao": "tramitar",
            "status_novo": Solicitacao.Status.EM_ANALISE,
            "observacao": "Processo recebido pela equipe de triagem.",
        },
    )
    client.post(
        detalhe_url,
        data={
            "acao": "tramitar",
            "status_novo": Solicitacao.Status.CONCLUIDA,
            "observacao": "Cadastro atualizado com sucesso.",
        },
    )
    solicitacao.refresh_from_db()
    assert solicitacao.status == Solicitacao.Status.CONCLUIDA
    assert solicitacao.concluido_em is not None

    # RF04: Avaliação após conclusão
    client.post(
        detalhe_url,
        data={
            "acao": "avaliar",
            "nota": 5,
            "comentario": "Atendimento ágil e objetivo.",
        },
    )
    assert AvaliacaoConclusao.objects.filter(solicitacao=solicitacao, nota=5).exists()


@pytest.mark.django_db
def test_bloqueia_transicao_invalida_e_avaliacao_antes_da_conclusao():
    solicitacao = Solicitacao.objects.create(
        titulo="Ajuste de permissão",
        descricao="Solicitação para ajuste de perfil de usuário no sistema.",
        nome_solicitante="Bruno Costa",
        email_solicitante="bruno@exemplo.com",
    )

    tramitacao_invalida = TramitacaoForm(
        data={"status_novo": Solicitacao.Status.CONCLUIDA, "observacao": "Tentativa direta"},
        solicitacao=solicitacao,
    )
    assert not tramitacao_invalida.is_valid()

    avaliacao_prematura = AvaliacaoConclusaoForm(
        data={"nota": 4, "comentario": "Ainda aberta"},
        solicitacao=solicitacao,
    )
    assert not avaliacao_prematura.is_valid()
