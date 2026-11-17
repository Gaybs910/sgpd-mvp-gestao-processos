import uuid
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    class Perfil(models.TextChoices):
        SOLICITANTE = "SOLICITANTE", "Solicitante"
        ATENDENTE = "ATENDENTE", "Atendente"
        GESTOR = "GESTOR", "Gestor"

    perfil = models.CharField(
        max_length=20,
        choices=Perfil.choices,
        default=Perfil.SOLICITANTE,
        verbose_name="Perfil de acesso",
    )
    departamento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Departamento",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} ({self.get_perfil_display()})"


class Solicitacao(models.Model):
    class Categoria(models.TextChoices):
        ADMINISTRATIVO = "ADMINISTRATIVO", "Administrativo"
        TI = "TI", "Tecnologia da Informação"
        ACADEMICO = "ACADEMICO", "Acadêmico"
        FINANCEIRO = "FINANCEIRO", "Financeiro"
        OUTROS = "OUTROS", "Outros"

    class Prioridade(models.TextChoices):
        BAIXA = "BAIXA", "Baixa"
        MEDIA = "MEDIA", "Média"
        ALTA = "ALTA", "Alta"
        URGENTE = "URGENTE", "Urgente"

    class Status(models.TextChoices):
        ABERTA = "ABERTA", "Aberta"
        EM_ANALISE = "EM_ANALISE", "Em análise"
        EM_ATENDIMENTO = "EM_ATENDIMENTO", "Em atendimento"
        CONCLUIDA = "CONCLUIDA", "Concluída"
        CANCELADA = "CANCELADA", "Cancelada"

    protocolo = models.CharField(
        max_length=24,
        unique=True,
        editable=False,
        verbose_name="Protocolo",
    )
    titulo = models.CharField(max_length=150, verbose_name="Título da solicitação")
    descricao = models.TextField(verbose_name="Descrição detalhada")
    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.ADMINISTRATIVO,
        verbose_name="Categoria",
    )
    prioridade = models.CharField(
        max_length=15,
        choices=Prioridade.choices,
        default=Prioridade.MEDIA,
        verbose_name="Prioridade",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ABERTA,
        verbose_name="Status atual",
    )
    nome_solicitante = models.CharField(max_length=120, verbose_name="Nome do solicitante")
    email_solicitante = models.EmailField(verbose_name="E-mail do solicitante")
    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitacoes_criadas",
        verbose_name="Usuário solicitante",
    )
    responsavel = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitacoes_atribuidas",
        verbose_name="Responsável pelo atendimento",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    concluido_em = models.DateTimeField(null=True, blank=True, verbose_name="Concluído em")

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Solicitação"
        verbose_name_plural = "Solicitações"
        indexes = [
            models.Index(fields=["protocolo"]),
            models.Index(fields=["status", "prioridade"]),
        ]

    @staticmethod
    def gerar_protocolo() -> str:
        ano = timezone.now().year
        sufixo = uuid.uuid4().hex[:6].upper()
        return f"SGPD-{ano}-{sufixo}"

    def save(self, *args, **kwargs):
        if not self.protocolo:
            candidato = self.gerar_protocolo()
            while Solicitacao.objects.filter(protocolo=candidato).exists():
                candidato = self.gerar_protocolo()
            self.protocolo = candidato
        if self.status == self.Status.CONCLUIDA and self.concluido_em is None:
            self.concluido_em = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.protocolo} - {self.titulo}"


class HistoricoTramitacao(models.Model):
    solicitacao = models.ForeignKey(
        Solicitacao,
        on_delete=models.CASCADE,
        related_name="historico",
        verbose_name="Solicitação",
    )
    autor = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tramitacoes_realizadas",
        verbose_name="Autor da movimentação",
    )
    status_anterior = models.CharField(
        max_length=20,
        choices=Solicitacao.Status.choices,
        blank=True,
        verbose_name="Status anterior",
    )
    status_novo = models.CharField(
        max_length=20,
        choices=Solicitacao.Status.choices,
        verbose_name="Novo status",
    )
    observacao = models.TextField(verbose_name="Observação da tramitação")
    registrado_em = models.DateTimeField(auto_now_add=True, verbose_name="Registrado em")

    class Meta:
        ordering = ["registrado_em"]
        verbose_name = "Histórico de tramitação"
        verbose_name_plural = "Históricos de tramitação"

    def __str__(self) -> str:
        return f"{self.solicitacao.protocolo}: {self.status_anterior or 'INÍCIO'} -> {self.status_novo}"


class AvaliacaoConclusao(models.Model):
    solicitacao = models.OneToOneField(
        Solicitacao,
        on_delete=models.CASCADE,
        related_name="avaliacao",
        verbose_name="Solicitação",
    )
    nota = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Nota (1 a 5)",
    )
    comentario = models.TextField(blank=True, verbose_name="Comentário")
    avaliado_em = models.DateTimeField(auto_now_add=True, verbose_name="Avaliado em")

    class Meta:
        verbose_name = "Avaliação de conclusão"
        verbose_name_plural = "Avaliações de conclusão"

    def __str__(self) -> str:
        return f"{self.solicitacao.protocolo} - Nota {self.nota}/5"
