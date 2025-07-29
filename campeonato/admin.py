from django.contrib import admin
from .models import (
    Time, Jogador, Profissional, Campeonato, 
    TimeCampeonato, JogadorTimeCampeonato, ProfissionalCampeonato,
    Rodada, Partida, ProfissionalPartida, Gol, Cartao, Despesa
)


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'ano_fundacao', 'tenant')
    list_filter = ('cidade', 'tenant')
    search_fields = ('nome', 'cidade')


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_nascimento', 'cidade', 'telefone', 'tenant')
    list_filter = ('cidade', 'tenant')
    search_fields = ('nome', 'cidade', 'titulo_eleitor')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tenant', 'nome', 'foto', 'data_nascimento', 'telefone')
        }),
        ('Endereço', {
            'fields': ('cidade', 'logradouro', 'bairro', 'cep', 'complemento')
        }),
        ('Informações Eleitorais', {
            'fields': ('titulo_eleitor', 'zona_eleitoral', 'secao_eleitoral')
        }),
    )


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'cidade', 'federacao', 'liga', 'tipo_chave_pix', 'telefone', 'tenant')
    list_filter = ('cidade', 'federacao', 'tipo_chave_pix', 'tenant')
    search_fields = ('nome', 'cpf', 'federacao', 'liga')
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'cpf', 'cidade', 'telefone')
        }),
        ('Informações Profissionais', {
            'fields': ('federacao', 'liga')
        }),
        ('Dados PIX', {
            'fields': ('tipo_chave_pix', 'chave_pix')
        }),
    )


@admin.register(Campeonato)
class CampeonatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'edicao', 'organizador', 'data_inicio', 'permite_transferencia', 'tenant')
    list_filter = ('permite_transferencia', 'tenant')
    search_fields = ('nome', 'edicao', 'organizador')


class JogadorTimeCampeonatoInline(admin.TabularInline):
    model = JogadorTimeCampeonato
    extra = 1
    autocomplete_fields = ['jogador']


@admin.register(TimeCampeonato)
class TimeCampeonatoAdmin(admin.ModelAdmin):
    list_display = ('time', 'campeonato', 'data_inscricao')
    list_filter = ('campeonato',)
    search_fields = ('time__nome', 'campeonato__nome')
    autocomplete_fields = ['time', 'campeonato']
    inlines = [JogadorTimeCampeonatoInline]


@admin.register(JogadorTimeCampeonato)
class JogadorTimeCampeonatoAdmin(admin.ModelAdmin):
    list_display = ('jogador', 'time_campeonato', 'data_entrada', 'data_saida', 'ativo')
    list_filter = ('ativo', 'time_campeonato__campeonato')
    search_fields = ('jogador__nome', 'time_campeonato__time__nome')
    autocomplete_fields = ['jogador', 'time_campeonato']


@admin.register(ProfissionalCampeonato)
class ProfissionalCampeonatoAdmin(admin.ModelAdmin):
    list_display = ('profissional', 'campeonato')
    list_filter = ('campeonato',)
    search_fields = ('profissional__nome', 'campeonato__nome')
    autocomplete_fields = ['profissional', 'campeonato']


class PartidaInline(admin.TabularInline):
    model = Partida
    extra = 1


@admin.register(Rodada)
class RodadaAdmin(admin.ModelAdmin):
    list_display = ('campeonato', 'numero', 'data')
    list_filter = ('campeonato',)
    search_fields = ('campeonato__nome', 'observacoes')
    inlines = [PartidaInline]


class GolInline(admin.TabularInline):
    model = Gol
    extra = 1


class CartaoInline(admin.TabularInline):
    model = Cartao
    extra = 1


class ProfissionalPartidaInline(admin.TabularInline):
    model = ProfissionalPartida
    extra = 1
    autocomplete_fields = ['profissional_campeonato']


class DespesaInline(admin.TabularInline):
    model = Despesa
    extra = 1


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'rodada', 'data_hora', 'local', 'encerrada')
    list_filter = ('rodada__campeonato', 'encerrada')
    search_fields = ('local', 'time_mandante__time__nome', 'time_visitante__time__nome')
    autocomplete_fields = ['rodada', 'time_mandante', 'time_visitante']
    inlines = [GolInline, CartaoInline, ProfissionalPartidaInline]


@admin.register(ProfissionalPartida)
class ProfissionalPartidaAdmin(admin.ModelAdmin):
    list_display = ('profissional_campeonato', 'partida', 'funcao', 'valor', 'descricao')
    list_filter = ('funcao', 'partida__rodada__campeonato')
    search_fields = ('profissional_campeonato__profissional__nome', 'descricao')
    inlines = [DespesaInline]


@admin.register(Gol)
class GolAdmin(admin.ModelAdmin):
    list_display = ('jogador', 'partida', 'time', 'minuto', 'tipo')
    list_filter = ('tipo', 'partida__rodada__campeonato')
    search_fields = ('jogador__jogador__nome', 'partida__time_mandante__time__nome', 'partida__time_visitante__time__nome')


@admin.register(Cartao)
class CartaoAdmin(admin.ModelAdmin):
    list_display = ('jogador', 'partida', 'tipo', 'minuto')
    list_filter = ('tipo', 'partida__rodada__campeonato')
    search_fields = ('jogador__jogador__nome', 'motivo')


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'profissional_partida', 'valor')
    list_filter = ('profissional_partida__partida__rodada__campeonato',)
    search_fields = ('descricao', 'profissional_partida__profissional_campeonato__profissional__nome')
