import hashlib
import html
import re
import pytest


class SGPDService:
    def __init__(self):
        self.usuarios = {}
        self.solicitacoes = {}
        self.historico = []
        self.avaliacoes = {}

    def cadastrar_operador(self, email: str, senha: str):
        salt = "sgpd_salt_2026"
        senha_hash = "pbkdf2_sha256$" + hashlib.pbkdf2_hmac(
            "sha256", senha.encode(), salt.encode(), 100000
        ).hex()
        self.usuarios[email] = {"email": email, "senha_hash": senha_hash, "ativo": True}
        return self.usuarios[email]

    def abrir_solicitacao(self, nome: str, contato: str, categoria: str, descricao: str):
        if not all([nome.strip(), contato.strip(), categoria.strip(), descricao.strip()]):
            raise ValueError("Todos os campos obrigatórios devem ser preenchidos.")
        protocolo = f"20261117-{len(self.solicitacoes) + 1:04d}"
        descricao_segura = html.escape(descricao)
        self.solicitacoes[protocolo] = {
            "protocolo": protocolo,
            "nome": nome,
            "contato": contato,
            "categoria": categoria,
            "descricao": descricao_segura,
            "status": "aberta",
        }
        self.historico.append({"protocolo": protocolo, "status": "aberta", "parecer": "Abertura registrada"})
        return self.solicitacoes[protocolo]

    def tramitar_solicitacao(self, protocolo: str, novo_status: str, parecer: str):
        if protocolo not in self.solicitacoes:
            raise KeyError("Protocolo não encontrado.")
        if not parecer or not parecer.strip():
            raise ValueError("Parecer técnico é obrigatório para alterar status.")
        self.solicitacoes[protocolo]["status"] = novo_status
        self.historico.append({"protocolo": protocolo, "status": novo_status, "parecer": html.escape(parecer)})
        return self.solicitacoes[protocolo]

    def registrar_avaliacao(self, protocolo: str, nota: int, comentario: str = ""):
        if self.solicitacoes[protocolo]["status"] != "concluida":
            raise PermissionError("Avaliação permitida apenas após conclusão.")
        if protocolo in self.avaliacoes:
            raise ValueError("Este protocolo já foi avaliado.")
        if nota not in (1, 2, 3, 4, 5):
            raise ValueError("Nota deve estar entre 1 e 5.")
        self.avaliacoes[protocolo] = {"nota": nota, "comentario": html.escape(comentario)}
        return self.avaliacoes[protocolo]


def test_rf01_abertura_solicitacao_e_historico():
    sgpd = SGPDService()
    sol = sgpd.abrir_solicitacao("Mariana Costa", "mariana@exemplo.org", "Manutenção", "Luz queimada")
    assert sol["protocolo"] == "20261117-0001"
    assert sol["status"] == "aberta"
    assert len(sgpd.historico) == 1


def test_rf03_tramitacao_exige_parecer_obrigatorio():
    sgpd = SGPDService()
    sol = sgpd.abrir_solicitacao("Mariana Costa", "mariana@exemplo.org", "Manutenção", "Luz queimada")
    with pytest.raises(ValueError):
        sgpd.tramitar_solicitacao(sol["protocolo"], "em_andamento", "")
    atualizada = sgpd.tramitar_solicitacao(sol["protocolo"], "concluida", "Lâmpada trocada.")
    assert atualizada["status"] == "concluida"


def test_rf04_avaliacao_unica_pos_conclusao():
    sgpd = SGPDService()
    sol = sgpd.abrir_solicitacao("Mariana Costa", "mariana@exemplo.org", "Manutenção", "Luz queimada")
    sgpd.tramitar_solicitacao(sol["protocolo"], "concluida", "Serviço finalizado.")
    av = sgpd.registrar_avaliacao(sol["protocolo"], 5, "Excelente!")
    assert av["nota"] == 5
    with pytest.raises(ValueError):
        sgpd.registrar_avaliacao(sol["protocolo"], 4, "Tentativa duplicada")


def test_rnf01_rnf02_hash_robusto_e_protecao_xss():
    sgpd = SGPDService()
    op = sgpd.cadastrar_operador("carlos@sgpd.org", "SenhaSegura123")
    assert op["senha_hash"] != "SenhaSegura123"
    assert op["senha_hash"].startswith("pbkdf2_sha256$")

    sol = sgpd.abrir_solicitacao("Teste", "t@t.com", "Geral", "<script>alert(1)</script>")
    assert "<script>" not in sol["descricao"]
    assert "&lt;script&gt;" in sol["descricao"]