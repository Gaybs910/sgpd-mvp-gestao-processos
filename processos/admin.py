from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AvaliacaoConclusao, HistoricoTramitacao, Solicitacao, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Dados SGPD", {"fields": ("perfil", "departamento")}),
    )
    list_display = ("username", "email", "perfil", "departamento", "is_staff")
    list_filter = ("perfil", "is_staff", "is_active")


class HistoricoInline(admin.TabularInline):
    model = HistoricoTramitacao
    extra = 0
    readonly_fields = ("status_anterior", "status_novo", "observacao", "autor", "registrado_em")


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ("protocolo", "titulo", "categoria", "prioridade", "status", "nome_solicitante", "criado_em")
    list_filter = ("status", "categoria", "prioridade")
    search_fields = ("protocolo", "titulo", "nome_solicitante", "email_solicitante")
    readonly_fields = ("protocolo", "criado_em", "atualizado_em", "concluido_em")
    inlines = [HistoricoInline]


@admin.register(HistoricoTramitacao)
class HistoricoTramitacaoAdmin(admin.ModelAdmin):
    list_display = ("solicitacao", "status_anterior", "status_novo", "autor", "registrado_em")
    list_filter = ("status_novo",)
    search_fields = ("solicitacao__protocolo", "observacao")


@admin.register(AvaliacaoConclusao)
class AvaliacaoConclusaoAdmin(admin.ModelAdmin):
    list_display = ("solicitacao", "nota", "avaliado_em")
    list_filter = ("nota",)
    search_fields = ("solicitacao__protocolo",)
